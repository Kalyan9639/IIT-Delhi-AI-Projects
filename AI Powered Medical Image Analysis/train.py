import os
import json
import argparse
import glob
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV3Small
from tensorflow.keras import layers, models
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, classification_report
)
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def parse_args():
    parser = argparse.ArgumentParser(description="Train MobileNetV3Small on Chest X-Ray dataset")
    parser.add_argument(
        "--method",
        type=str,
        choices=["oversample", "undersample", "class_weights"],
        default="oversample",
        help="Method to handle class imbalance (default: oversample)"
    )
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--data_dir", type=str, default="chest_xray", help="Path to the chest_xray dataset")
    return parser.parse_args()


def process_path(file_path, label):
    img = tf.io.read_file(file_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [224, 224])
    return img, label


def create_dataset(paths, labels, batch_size=32, is_training=True):
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if is_training:
        dataset = dataset.shuffle(buffer_size=len(paths))
    dataset = dataset.map(process_path, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset


def main():
    args = parse_args()
    logging.info(f"Starting training process using imbalance handling method: {args.method}")

    data_dir = args.data_dir
    train_dir = os.path.join(data_dir, "train")
    val_dir   = os.path.join(data_dir, "val")
    test_dir  = os.path.join(data_dir, "test")

    # ------------------------------------------------------------------
    # Load paths
    # ------------------------------------------------------------------
    train_normal    = glob.glob(os.path.join(train_dir, 'NORMAL',    '*.*'))
    train_pneumonia = glob.glob(os.path.join(train_dir, 'PNEUMONIA', '*.*'))
    logging.info(f"Original Training Samples - Normal: {len(train_normal)}, Pneumonia: {len(train_pneumonia)}")

    if args.method == 'oversample':
        # Only the MINORITY class is oversampled by duplicating its samples.
        # The MAJORITY class is kept exactly as-is — no resampling or removal.
        if len(train_normal) < len(train_pneumonia):
            # Normal is minority — add duplicates until it matches Pneumonia count
            shortage = len(train_pneumonia) - len(train_normal)
            train_normal = train_normal + random.choices(train_normal, k=shortage)
        elif len(train_pneumonia) < len(train_normal):
            # Pneumonia is minority — add duplicates until it matches Normal count
            shortage = len(train_normal) - len(train_pneumonia)
            train_pneumonia = train_pneumonia + random.choices(train_pneumonia, k=shortage)
        logging.info(f"After oversampling (minority only) - Normal: {len(train_normal)}, Pneumonia: {len(train_pneumonia)}")

    elif args.method == 'undersample':
        # Only the MAJORITY class is undersampled (randomly dropped).
        # The MINORITY class is kept exactly as-is.
        if len(train_normal) > len(train_pneumonia):
            train_normal = random.sample(train_normal, len(train_pneumonia))
        elif len(train_pneumonia) > len(train_normal):
            train_pneumonia = random.sample(train_pneumonia, len(train_normal))
        logging.info(f"After undersampling (majority only) - Normal: {len(train_normal)}, Pneumonia: {len(train_pneumonia)}")

    train_paths  = train_normal + train_pneumonia
    train_labels = [0] * len(train_normal) + [1] * len(train_pneumonia)

    # Shuffle lists synchronously
    temp = list(zip(train_paths, train_labels))
    random.shuffle(temp)
    train_paths, train_labels = zip(*temp)
    train_paths, train_labels = list(train_paths), list(train_labels)

    class_weight_dict = None
    if args.method == 'class_weights':
        classes        = np.array(train_labels)
        unique_classes = np.unique(classes)
        weights        = compute_class_weight('balanced', classes=unique_classes, y=classes)
        class_weight_dict = dict(zip(unique_classes, weights))
        logging.info(f"Calculated Class Weights: {class_weight_dict}")

    train_dataset = create_dataset(train_paths, train_labels, batch_size=args.batch_size, is_training=True)

    # Val Data
    val_normal    = glob.glob(os.path.join(val_dir, 'NORMAL',    '*.*'))
    val_pneumonia = glob.glob(os.path.join(val_dir, 'PNEUMONIA', '*.*'))
    val_paths     = val_normal + val_pneumonia
    val_labels    = [0] * len(val_normal) + [1] * len(val_pneumonia)
    val_dataset   = create_dataset(val_paths, val_labels, batch_size=args.batch_size, is_training=False)

    # Test Data
    test_normal    = glob.glob(os.path.join(test_dir, 'NORMAL',    '*.*'))
    test_pneumonia = glob.glob(os.path.join(test_dir, 'PNEUMONIA', '*.*'))
    test_paths     = test_normal + test_pneumonia
    test_labels    = [0] * len(test_normal) + [1] * len(test_pneumonia)
    test_dataset   = create_dataset(test_paths, test_labels, batch_size=args.batch_size, is_training=False)

    logging.info("Datasets prepared. Building model.")

    # ------------------------------------------------------------------
    # MobileNetV3Small Architecture
    # ------------------------------------------------------------------
    base_model = MobileNetV3Small(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Freeze base model

    inputs  = layers.Input(shape=(224, 224, 3))
    x       = tf.keras.applications.mobilenet_v3.preprocess_input(inputs)
    x       = base_model(x, training=False)
    x       = layers.GlobalAveragePooling2D()(x)
    x       = layers.Dense(128, activation='relu')(x)
    x       = layers.Dropout(0.2)(x)
    outputs = layers.Dense(1, activation='sigmoid')(x)

    model = models.Model(inputs, outputs)

    # Use proper stateful Keras metrics during training.
    # NOTE: The broken function-based F1 metric has been intentionally removed.
    #       Keras averages per-batch F1 values which produces impossible scores >1.
    #       True F1 is computed via sklearn after training on the full test set.
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss='binary_crossentropy',
        metrics=[
            'accuracy',
            tf.keras.metrics.Precision(name='precision'),
            tf.keras.metrics.Recall(name='recall'),
        ]
    )

    logging.info("Starting training...")
    model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=args.epochs,
        class_weight=class_weight_dict
    )

    # ------------------------------------------------------------------
    # Final evaluation using sklearn — guaranteed to be correct
    # ------------------------------------------------------------------
    logging.info("Running sklearn evaluation on test set (reliable metrics)...")

    y_pred_proba = model.predict(test_dataset, verbose=1)
    y_pred       = (y_pred_proba.flatten() >= 0.5).astype(int)
    y_true       = np.array(test_labels)

    acc       = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall    = recall_score(y_true, y_pred, zero_division=0)
    f1        = f1_score(y_true, y_pred, zero_division=0)

    logging.info("=" * 55)
    logging.info("  FINAL TEST METRICS (sklearn — trustworthy)")
    logging.info("=" * 55)
    logging.info(f"  Accuracy  : {acc:.4f}  ({acc*100:.2f}%)")
    logging.info(f"  Precision : {precision:.4f}")
    logging.info(f"  Recall    : {recall:.4f}")
    logging.info(f"  F1-Score  : {f1:.4f}")
    logging.info("=" * 55)

    logging.info("\nDetailed Classification Report:\n" +
                 classification_report(y_true, y_pred,
                                       target_names=["NORMAL", "PNEUMONIA"]))

    # ------------------------------------------------------------------
    # Save model + metrics to artifacts/
    # ------------------------------------------------------------------
    os.makedirs("artifacts", exist_ok=True)

    model_name = f"chest_xray_pneumonia_{args.method}.keras"
    save_path  = os.path.join("artifacts", model_name)
    model.save(save_path)
    logging.info(f"Model saved to {save_path}")

    # Per-class metrics from sklearn classification report
    report = classification_report(
        y_true, y_pred,
        target_names=["NORMAL", "PNEUMONIA"],
        output_dict=True,
        zero_division=0
    )

    metrics = {
        "method":  args.method,
        "epochs":  args.epochs,
        "test_samples": {
            "normal":    len(test_normal),
            "pneumonia": len(test_pneumonia),
            "total":     len(test_labels),
        },
        "overall": {
            "accuracy":         round(float(acc),       4),
            "macro_precision":  round(float(report["macro avg"]["precision"]),  4),
            "macro_recall":     round(float(report["macro avg"]["recall"]),     4),
            "macro_f1_score":   round(float(report["macro avg"]["f1-score"]),   4),
            "weighted_precision": round(float(report["weighted avg"]["precision"]),  4),
            "weighted_recall":    round(float(report["weighted avg"]["recall"]),     4),
            "weighted_f1_score":  round(float(report["weighted avg"]["f1-score"]),   4),
        },
        "per_class": {
            "NORMAL": {
                "precision": round(float(report["NORMAL"]["precision"]),  4),
                "recall":    round(float(report["NORMAL"]["recall"]),     4),
                "f1_score":  round(float(report["NORMAL"]["f1-score"]),   4),
                "support":   int(report["NORMAL"]["support"]),
            },
            "PNEUMONIA": {
                "precision": round(float(report["PNEUMONIA"]["precision"]),  4),
                "recall":    round(float(report["PNEUMONIA"]["recall"]),     4),
                "f1_score":  round(float(report["PNEUMONIA"]["f1-score"]),   4),
                "support":   int(report["PNEUMONIA"]["support"]),
            },
        }
    }

    metrics_path = os.path.join("artifacts", "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)
    logging.info(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
