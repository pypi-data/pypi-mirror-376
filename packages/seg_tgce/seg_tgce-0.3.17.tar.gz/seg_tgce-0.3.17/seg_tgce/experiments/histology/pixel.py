import argparse

from keras import Model
from keras.callbacks import EarlyStopping, ReduceLROnPlateau

from seg_tgce.data.crowd_seg.tfds_builder import (
    N_CLASSES,
    N_REAL_SCORERS,
    get_processed_data,
)
from seg_tgce.experiments.plot_utils import plot_training_history, print_test_metrics
from seg_tgce.experiments.types import HpTunerTrial
from seg_tgce.experiments.utils import handle_training_optuna
from seg_tgce.models.builders import build_pixel_model_from_hparams
from seg_tgce.models.ma_model import PixelVisualizationCallback

TARGET_SHAPE = (256, 256)
BATCH_SIZE = 8
TRAIN_EPOCHS = 50
TUNER_EPOCHS = 10
MAX_TRIALS = 10
STUDY_NAME = "histology_pixel_tuning"
OBJECTIVE = "val_segmentation_output_dice_coefficient"

DEFAULT_HPARAMS = {
    "initial_learning_rate": 6.5e-4,
    "q": 0.66,
    "noise_tolerance": 0.62,
    "a": 0.2,
    "b": 0.7,
    "lambda_reg_weight": 0.1,
    "lambda_entropy_weight": 0.1,
    "lambda_sum_weight": 0.1,
}


def build_model_from_trial(trial: HpTunerTrial | None) -> Model:
    if trial is None:
        return build_pixel_model_from_hparams(
            learning_rate=DEFAULT_HPARAMS["initial_learning_rate"],
            q=DEFAULT_HPARAMS["q"],
            noise_tolerance=DEFAULT_HPARAMS["noise_tolerance"],
            b=DEFAULT_HPARAMS["b"],
            a=DEFAULT_HPARAMS["a"],
            lambda_reg_weight=DEFAULT_HPARAMS["lambda_reg_weight"],
            lambda_entropy_weight=DEFAULT_HPARAMS["lambda_entropy_weight"],
            lambda_sum_weight=DEFAULT_HPARAMS["lambda_sum_weight"],
            num_classes=N_CLASSES,
            target_shape=TARGET_SHAPE,
            n_scorers=N_REAL_SCORERS,
        )

    return build_pixel_model_from_hparams(
        learning_rate=DEFAULT_HPARAMS["initial_learning_rate"],
        q=DEFAULT_HPARAMS["q"],
        noise_tolerance=DEFAULT_HPARAMS["noise_tolerance"],
        a=trial.suggest_float("a", 0.1, 10.0, step=0.1),
        b=trial.suggest_float("b", 0.1, 0.99, step=0.01),
        lambda_reg_weight=trial.suggest_float("lambda_reg_weight", 0.0, 10.0, step=0.1),
        lambda_entropy_weight=trial.suggest_float(
            "lambda_entropy_weight", 0.0, 10.0, step=0.1
        ),
        lambda_sum_weight=trial.suggest_float("lambda_sum_weight", 0.0, 10.0, step=0.1),
        num_classes=N_CLASSES,
        target_shape=TARGET_SHAPE,
        n_scorers=N_REAL_SCORERS,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train histology features model with or without hyperparameter tuning"
    )
    parser.add_argument(
        "--use-tuner",
        action="store_true",
        help="Use Keras Tuner for hyperparameter optimization",
    )
    args = parser.parse_args()

    processed_train, processed_validation, processed_test = get_processed_data(
        image_size=TARGET_SHAPE,
        batch_size=BATCH_SIZE,
        use_augmentation=True,
        augmentation_factor=2,
    )

    model, study = handle_training_optuna(
        processed_train,
        processed_validation,
        model_builder=build_model_from_trial,
        use_tuner=args.use_tuner,
        tuner_epochs=TUNER_EPOCHS,
        objective=OBJECTIVE,
        tuner_max_trials=MAX_TRIALS,
        study_name=STUDY_NAME,
    )

    vis_callback = PixelVisualizationCallback(
        processed_validation, save_dir="vis/histology/features"
    )

    lr_scheduler = ReduceLROnPlateau(
        monitor=OBJECTIVE,
        factor=0.5,
        patience=3,
        min_lr=1e-6,
        mode="max",
        verbose=1,
    )

    print("\nTraining final model...")

    history = model.fit(
        processed_train,
        epochs=TRAIN_EPOCHS,
        validation_data=processed_validation,
        callbacks=[
            vis_callback,
            lr_scheduler,
            EarlyStopping(
                monitor=OBJECTIVE,
                patience=5,
                mode="max",
                restore_best_weights=True,
            ),
        ],
    )

    plot_training_history(history, "Histology Pixel Model Training History")
    print_test_metrics(model, processed_test, "Histology Pixel")
