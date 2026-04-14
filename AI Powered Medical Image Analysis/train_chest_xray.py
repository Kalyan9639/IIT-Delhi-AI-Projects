"""Train and evaluate a chest X-ray pneumonia classifier.

The dataset is expected to follow the common chest_xray layout:

    chest_xray/
      train/
        NORMAL/
        PNEUMONIA/
      val/
        NORMAL/
        PNEUMONIA/
      test/
        NORMAL/
        PNEUMONIA/

The script prefers the cleanest available dataset root automatically, so it
works with either an outer wrapper folder or a nested archive extraction.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf


IMAGE_SIZE = (224, 224)
CLASS_NAMES = ("NORMAL", "PNEUMONIA")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
AUTOTUNE = tf.data.AUTOTUNE
BALANCE_STRATEGIES = {
    "class_weights",
    "undersample_pneumonia",
    "oversample_normal",
}


@dataclass
class SplitSummary:
    normal: int
    pneumonia: int

    @property
    def total(self) -> int:
        return self.normal + self.pneumonia


@dataclass
class DatasetSummary:
    root: str
    train: SplitSummary
    val: SplitSummary
    test: SplitSummary


@dataclass
class TrainingConfig:
    backbone: str
    balance_strategy: str
    batch_size: int
    epochs: int
    fine_tune_epochs: int
    fine_tune_layers: int
    learning_rate: float
    fine_tune_learning_rate: float
    seed: int
    augmentation: str = "flip-rotation-zoom-contrast"


@dataclass
class EffectiveTrainSummary:
    strategy: str
    normal: int
    pneumonia: int

    @property
    def total(self) -> int:
        return self.normal + self.pneumonia


def count_image_files(folder: Path) -> int:
    return sum(
        1
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def count_split(folder: Path) -> SplitSummary:
    normal = count_image_files(folder / "NORMAL")
    pneumonia = count_image_files(folder / "PNEUMONIA")
    return SplitSummary(normal=normal, pneumonia=pneumonia)


def list_image_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def resolve_dataset_root(preferred_root: Path) -> Path:
    candidates = [preferred_root, preferred_root / "chest_xray"]
    scored: list[tuple[int, int, Path]] = []

    for candidate in candidates:
        train_dir = candidate / "train"
        val_dir = candidate / "val"
        test_dir = candidate / "test"
        class_dirs = [train_dir / "NORMAL", train_dir / "PNEUMONIA", val_dir / "NORMAL", val_dir / "PNEUMONIA", test_dir / "NORMAL", test_dir / "PNEUMONIA"]

        if not all(path.exists() for path in class_dirs):
            continue

        hidden_files = sum(
            1
            for path in candidate.rglob("*")
            if path.is_file() and path.name.startswith(".")
        )
        image_count = (
            count_image_files(train_dir)
            + count_image_files(val_dir)
            + count_image_files(test_dir)
        )
        scored.append((hidden_files, -image_count, candidate))

    if not scored:
        raise FileNotFoundError(
            f"Could not find a valid chest X-ray dataset under: {preferred_root}"
        )

    scored.sort()
    return scored[0][2]


def build_dataset_summary(root: Path) -> DatasetSummary:
    return DatasetSummary(
        root=str(root),
        train=count_split(root / "train"),
        val=count_split(root / "val"),
        test=count_split(root / "test"),
    )


def print_dataset_summary(summary: DatasetSummary) -> None:
    print(f"Dataset root: {summary.root}")
    for split_name in ("train", "val", "test"):
        split = getattr(summary, split_name)
        print(
            f"{split_name:>5}: NORMAL={split.normal}, "
            f"PNEUMONIA={split.pneumonia}, TOTAL={split.total}"
        )


def make_eval_datasets(
    root: Path,
    batch_size: int,
    seed: int,
) -> tuple[tf.data.Dataset, tf.data.Dataset]:
    common_kwargs = dict(
        image_size=IMAGE_SIZE,
        batch_size=batch_size,
        class_names=list(CLASS_NAMES),
        label_mode="binary",
        seed=seed,
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        root / "val",
        shuffle=False,
        **common_kwargs,
    )
    test_ds = tf.keras.utils.image_dataset_from_directory(
        root / "test",
        shuffle=False,
        **common_kwargs,
    )

    return val_ds.prefetch(AUTOTUNE), test_ds.prefetch(AUTOTUNE)


def load_image_from_path(path: tf.Tensor) -> tf.Tensor:
    image_bytes = tf.io.read_file(path)
    image = tf.image.decode_image(image_bytes, channels=3, expand_animations=False)
    image = tf.image.resize(image, IMAGE_SIZE)
    return tf.cast(image, tf.float32)


def build_train_dataset(
    root: Path,
    batch_size: int,
    seed: int,
    balance_strategy: str,
) -> tuple[tf.data.Dataset, EffectiveTrainSummary, Dict[int, float]]:
    train_root = root / "train"
    normal_files = list_image_files(train_root / "NORMAL")
    pneumonia_files = list_image_files(train_root / "PNEUMONIA")
    rng = np.random.default_rng(seed)

    if balance_strategy == "class_weights":
        selected_normal = normal_files
        selected_pneumonia = pneumonia_files
        class_weights = compute_class_weights(
            SplitSummary(normal=len(selected_normal), pneumonia=len(selected_pneumonia))
        )
    elif balance_strategy == "undersample_pneumonia":
        selected_normal = normal_files
        selected_pneumonia = rng.choice(
            pneumonia_files,
            size=len(normal_files),
            replace=False,
        ).tolist()
        class_weights = {0: 1.0, 1: 1.0}
    elif balance_strategy == "oversample_normal":
        selected_normal = rng.choice(
            normal_files,
            size=len(pneumonia_files),
            replace=True,
        ).tolist()
        selected_pneumonia = pneumonia_files
        class_weights = {0: 1.0, 1: 1.0}
    else:
        raise ValueError(
            f"Unknown balance strategy: {balance_strategy}. "
            f"Expected one of: {sorted(BALANCE_STRATEGIES)}"
        )

    filepaths = [str(path) for path in selected_normal] + [str(path) for path in selected_pneumonia]
    labels = [0.0] * len(selected_normal) + [1.0] * len(selected_pneumonia)
    indices = rng.permutation(len(filepaths))
    filepaths = [filepaths[i] for i in indices]
    labels = [labels[i] for i in indices]

    dataset = tf.data.Dataset.from_tensor_slices((filepaths, labels))
    dataset = dataset.shuffle(buffer_size=len(filepaths), seed=seed, reshuffle_each_iteration=True)
    dataset = dataset.map(
        lambda path, label: (load_image_from_path(path), tf.cast(label, tf.float32)),
        num_parallel_calls=AUTOTUNE,
    )
    dataset = dataset.batch(batch_size).prefetch(AUTOTUNE)

    return (
        dataset,
        EffectiveTrainSummary(
            strategy=balance_strategy,
            normal=len(selected_normal),
            pneumonia=len(selected_pneumonia),
        ),
        class_weights,
    )


def compute_class_weights(train_split: SplitSummary) -> Dict[int, float]:
    total = train_split.total
    if train_split.normal == 0 or train_split.pneumonia == 0:
        return {0: 1.0, 1: 1.0}

    return {
        0: total / (2.0 * train_split.normal),
        1: total / (2.0 * train_split.pneumonia),
    }


def build_model() -> tf.keras.Model:
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.05),
            tf.keras.layers.RandomZoom(0.1),
            tf.keras.layers.RandomContrast(0.1),
        ],
        name="augmentation",
    )

    inputs = tf.keras.Input(shape=IMAGE_SIZE + (3,), name="image")
    x = augmentation(inputs)
    x = tf.keras.layers.Lambda(
        tf.keras.applications.mobilenet_v3.preprocess_input,
        name="mobilenetv3small_preprocess",
    )(x)

    base_model = tf.keras.applications.MobileNetV3Small(
        include_top=False,
        weights="imagenet",
        input_shape=IMAGE_SIZE + (3,),
    )
    base_model.trainable = False

    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D(name="avg_pool")(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="prediction")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="chest_xray_mobilenetv3small")
    setattr(model, "_base_model", base_model)
    return model


def compile_model(model: tf.keras.Model, learning_rate: float) -> None:
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )


def fine_tune_model(model: tf.keras.Model, trainable_layers: int, learning_rate: float) -> None:
    base_model = getattr(model, "_base_model", None)
    if base_model is None:
        return

    base_model.trainable = True
    if trainable_layers > 0:
        for layer in base_model.layers[:-trainable_layers]:
            layer.trainable = False

    compile_model(model, learning_rate=learning_rate)


def build_callbacks(output_dir: Path) -> list[tf.keras.callbacks.Callback]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(output_dir / "best_model.keras"),
            monitor="val_loss",
            save_best_only=True,
            save_weights_only=False,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=4,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-7,
        ),
    ]


def evaluate_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float]:
    y_pred = (y_prob >= threshold).astype(np.int32)
    y_true = y_true.astype(np.int32)

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    accuracy = (tp + tn) / max(len(y_true), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "true_negatives": float(tn),
        "false_positives": float(fp),
        "false_negatives": float(fn),
        "true_positives": float(tp),
    }


def predict_dataset(model: tf.keras.Model, dataset: tf.data.Dataset) -> tuple[np.ndarray, np.ndarray]:
    y_true_batches: list[np.ndarray] = []
    y_prob_batches: list[np.ndarray] = []

    for images, labels in dataset:
        probabilities = model.predict(images, verbose=0).reshape(-1)
        y_prob_batches.append(probabilities)
        y_true_batches.append(labels.numpy().reshape(-1))

    y_true = np.concatenate(y_true_batches) if y_true_batches else np.array([])
    y_prob = np.concatenate(y_prob_batches) if y_prob_batches else np.array([])
    return y_true, y_prob


def save_training_curves(history: tf.keras.callbacks.History, output_path: Path) -> None:
    history_data = history.history
    epochs = range(1, len(history_data.get("loss", [])) + 1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    if "accuracy" in history_data:
        axes[0].plot(epochs, history_data["accuracy"], label="train_accuracy")
    if "val_accuracy" in history_data:
        axes[0].plot(epochs, history_data["val_accuracy"], label="val_accuracy")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()

    if "loss" in history_data:
        axes[1].plot(epochs, history_data["loss"], label="train_loss")
    if "val_loss" in history_data:
        axes[1].plot(epochs, history_data["val_loss"], label="val_loss")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend()

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_confusion_matrix(y_true: np.ndarray, y_prob: np.ndarray, output_path: Path) -> None:
    y_pred = (y_prob >= 0.5).astype(np.int32)
    cm = np.array(
        [
            [int(np.sum((y_true == 0) & (y_pred == 0))), int(np.sum((y_true == 0) & (y_pred == 1)))],
            [int(np.sum((y_true == 1) & (y_pred == 0))), int(np.sum((y_true == 1) & (y_pred == 1)))],
        ]
    )

    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(cm, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set_xticks([0, 1], labels=list(CLASS_NAMES))
    ax.set_yticks([0, 1], labels=list(CLASS_NAMES))
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")

    for row in range(cm.shape[0]):
        for col in range(cm.shape[1]):
            ax.text(col, row, str(cm[row, col]), ha="center", va="center", color="black")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_metrics(metrics: dict[str, float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def build_run_name(config: TrainingConfig) -> str:
    return "_".join(
        [
            "chestxray",
            config.backbone.lower(),
            f"bal-{config.balance_strategy}",
        ]
    )


def save_model_metadata(
    output_path: Path,
    summary: DatasetSummary,
    config: TrainingConfig,
    effective_train: EffectiveTrainSummary,
    run_name: str,
    model_path: Path,
) -> None:
    metadata = {
        "run_name": run_name,
        "model_path": str(model_path),
        "backbone": config.backbone,
        "image_size": list(IMAGE_SIZE),
        "class_names": list(CLASS_NAMES),
        "threshold": 0.5,
        "training_config": asdict(config),
        "effective_train_distribution": asdict(effective_train),
        "dataset_root": summary.root,
        "dataset_summary": {
            "train": asdict(summary.train),
            "val": asdict(summary.val),
            "test": asdict(summary.test),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def train_pipeline(
    data_root: Path,
    output_dir: Path,
    batch_size: int,
    seed: int,
    epochs: int,
    fine_tune_epochs: int,
    fine_tune_layers: int,
    learning_rate: float,
    fine_tune_learning_rate: float,
    balance_strategy: str,
) -> dict[str, float]:
    tf.keras.utils.set_random_seed(seed)

    dataset_root = resolve_dataset_root(data_root)
    summary = build_dataset_summary(dataset_root)
    print_dataset_summary(summary)

    train_ds, effective_train, class_weights = build_train_dataset(
        dataset_root,
        batch_size=batch_size,
        seed=seed,
        balance_strategy=balance_strategy,
    )
    val_ds, test_ds = make_eval_datasets(
        dataset_root,
        batch_size=batch_size,
        seed=seed,
    )

    config = TrainingConfig(
        backbone="MobileNetV3Small",
        balance_strategy=balance_strategy,
        batch_size=batch_size,
        epochs=epochs,
        fine_tune_epochs=fine_tune_epochs,
        fine_tune_layers=fine_tune_layers,
        learning_rate=learning_rate,
        fine_tune_learning_rate=fine_tune_learning_rate,
        seed=seed,
    )
    run_name = build_run_name(config)
    run_dir = output_dir / "runs" / run_name
    latest_model_path = output_dir / "model.keras"
    latest_metadata_path = output_dir / "model_metadata.json"
    latest_dataset_summary_path = output_dir / "dataset_summary.json"
    latest_training_curve_path = output_dir / "plots" / "training_curves.png"
    latest_confusion_matrix_path = output_dir / "plots" / "confusion_matrix.png"
    latest_metrics_path = output_dir / "metrics" / "test_metrics.json"

    print(f"Run name: {run_name}")
    print(
        "Effective train distribution:",
        f"NORMAL={effective_train.normal}, PNEUMONIA={effective_train.pneumonia}, TOTAL={effective_train.total}",
    )
    print("Class weights:", class_weights)

    model = build_model()
    compile_model(model, learning_rate=learning_rate)

    callbacks = build_callbacks(run_dir / "checkpoints")

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1,
    )

    if fine_tune_epochs > 0:
        fine_tune_model(
            model,
            trainable_layers=fine_tune_layers,
            learning_rate=fine_tune_learning_rate,
        )
        ft_history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs + fine_tune_epochs,
            initial_epoch=len(history.history["loss"]),
            callbacks=callbacks,
            class_weight=class_weights,
            verbose=1,
        )
        for key, values in ft_history.history.items():
            history.history.setdefault(key, []).extend(values)

    run_dir.mkdir(parents=True, exist_ok=True)
    model_path = run_dir / f"{run_name}.keras"
    model.save(model_path)

    y_true, y_prob = predict_dataset(model, test_ds)
    metrics = evaluate_predictions(y_true, y_prob)

    save_training_curves(history, run_dir / "plots" / "training_curves.png")
    save_confusion_matrix(y_true, y_prob, run_dir / "plots" / "confusion_matrix.png")
    save_metrics(metrics, run_dir / "metrics" / "test_metrics.json")
    save_model_metadata(
        run_dir / "model_metadata.json",
        summary,
        config=config,
        effective_train=effective_train,
        run_name=run_name,
        model_path=model_path,
    )
    (run_dir / "dataset_summary.json").write_text(
        json.dumps(asdict(summary), indent=2),
        encoding="utf-8",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, latest_model_path)
    shutil.copy2(run_dir / "model_metadata.json", latest_metadata_path)
    shutil.copy2(run_dir / "dataset_summary.json", latest_dataset_summary_path)
    (output_dir / "metrics").mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(parents=True, exist_ok=True)
    shutil.copy2(run_dir / "metrics" / "test_metrics.json", latest_metrics_path)
    shutil.copy2(run_dir / "plots" / "training_curves.png", latest_training_curve_path)
    shutil.copy2(run_dir / "plots" / "confusion_matrix.png", latest_confusion_matrix_path)

    print(f"Saved model to: {model_path}")
    print(f"Updated latest model at: {latest_model_path}")

    print("Test metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a chest X-ray pneumonia classifier.")
    parser.add_argument("--data-root", type=Path, default=Path("chest_xray"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument(
        "--balance-strategy",
        type=str,
        default="class_weights",
        choices=sorted(BALANCE_STRATEGIES),
        help="How to handle class imbalance during training.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--fine-tune-epochs", type=int, default=4)
    parser.add_argument("--fine-tune-layers", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--fine-tune-learning-rate", type=float, default=1e-5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_pipeline(
        data_root=args.data_root,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        seed=args.seed,
        epochs=args.epochs,
        fine_tune_epochs=args.fine_tune_epochs,
        fine_tune_layers=args.fine_tune_layers,
        learning_rate=args.learning_rate,
        fine_tune_learning_rate=args.fine_tune_learning_rate,
        balance_strategy=args.balance_strategy,
    )


if __name__ == "__main__":
    main()
