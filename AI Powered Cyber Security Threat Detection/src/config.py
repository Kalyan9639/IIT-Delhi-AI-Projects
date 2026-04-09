from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

TRAIN_DATA_PATH = DATA_DIR / "UNSW_train.csv"
TEST_DATA_PATH = DATA_DIR / "UNSW_test.csv"
MODEL_PATH = MODELS_DIR / "cyber_threat_model.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"
CONFUSION_MATRIX_PATH = ARTIFACTS_DIR / "confusion_matrix.png"

ID_COLUMN = "id"
TARGET_COLUMN = "label"
ATTACK_CATEGORY_COLUMN = "attack_cat"

CATEGORICAL_COLUMNS = ["proto", "service", "state"]
ENGINEERED_COLUMNS = [
    "total_bytes",
    "total_packets",
    "byte_ratio",
    "packet_rate",
    "load_diff",
    "tcp_diff",
]

BASE_NUMERIC_COLUMNS = [
    "dur",
    "spkts",
    "dpkts",
    "sbytes",
    "dbytes",
    "rate",
    "sttl",
    "dttl",
    "sload",
    "dload",
    "sloss",
    "dloss",
    "sinpkt",
    "dinpkt",
    "sjit",
    "djit",
    "swin",
    "stcpb",
    "dtcpb",
    "dwin",
    "tcprtt",
    "synack",
    "ackdat",
    "smean",
    "dmean",
    "trans_depth",
    "response_body_len",
    "ct_srv_src",
    "ct_state_ttl",
    "ct_dst_ltm",
    "ct_src_dport_ltm",
    "ct_dst_sport_ltm",
    "ct_dst_src_ltm",
    "is_ftp_login",
    "ct_ftp_cmd",
    "ct_flw_http_mthd",
    "ct_src_ltm",
    "ct_srv_dst",
    "is_sm_ips_ports",
]


def ensure_directories() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

