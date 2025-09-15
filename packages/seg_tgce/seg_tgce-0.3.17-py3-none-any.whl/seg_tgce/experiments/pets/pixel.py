import argparse

from keras import Model
from keras.callbacks import EarlyStopping, ReduceLROnPlateau

from seg_tgce.data.oxford_pet.oxford_pet import (
    fetch_models,
    get_data_multiple_annotators,
)
from seg_tgce.experiments.plot_utils import plot_training_history, print_test_metrics
from seg_tgce.experiments.types import HpTunerTrial
from seg_tgce.experiments.utils import handle_training_optuna
from seg_tgce.models.builders import build_pixel_model_from_hparams
from seg_tgce.models.ma_model import PixelVisualizationCallback

TARGET_SHAPE = (256, 256)
BATCH_SIZE = 16
NUM_CLASSES = 3
NOISE_LEVELS = [-20.0, 10.0]
NUM_SCORERS = len(NOISE_LEVELS)
TRAIN_EPOCHS = 50
TUNER_EPOCHS = 1
TUNER_MAX_TRIALS = 1
STUDY_NAME = "pets_pixel_tuning"
OBJECTIVE = "val_segmentation_output_dice_coefficient"
LABELING_RATE = 1.0

DEFAULT_HPARAMS = {
    "initial_learning_rate": 1e-3,
    "q": 0.7,
    "noise_tolerance": 0.5,
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
            num_classes=NUM_CLASSES,
            target_shape=TARGET_SHAPE,
            n_scorers=NUM_SCORERS,
        )

    return build_pixel_model_from_hparams(
        learning_rate=trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True),
        q=trial.suggest_float("q", 0.1, 0.9, step=0.01),
        noise_tolerance=trial.suggest_float("noise_tolerance", 0.1, 0.9, step=0.01),
        a=trial.suggest_float("a", 0.1, 10.0, step=0.1),
        b=trial.suggest_float("b", 0.1, 0.99, step=0.01),
        lambda_reg_weight=trial.suggest_float("lambda_reg_weight", 0.0, 10.0, step=0.1),
        lambda_entropy_weight=trial.suggest_float(
            "lambda_entropy_weight", 0.0, 10.0, step=0.1
        ),
        lambda_sum_weight=trial.suggest_float("lambda_sum_weight", 0.0, 10.0, step=0.1),
        num_classes=NUM_CLASSES,
        target_shape=TARGET_SHAPE,
        n_scorers=NUM_SCORERS,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train pets pixel model with or without hyperparameter tuning"
    )
    parser.add_argument(
        "--use-tuner",
        action="store_true",
        help="Use Keras Tuner for hyperparameter optimization",
    )
    args = parser.parse_args()

    disturbance_models = fetch_models(NOISE_LEVELS)
    train, val, test = get_data_multiple_annotators(
        annotation_models=disturbance_models,
        target_shape=TARGET_SHAPE,
        batch_size=BATCH_SIZE,
        labeling_rate=LABELING_RATE,
    )

    model, study = handle_training_optuna(
        train.take(10).cache(),
        val.take(10).cache(),
        model_builder=build_model_from_trial,
        use_tuner=args.use_tuner,
        tuner_epochs=TUNER_EPOCHS,
        objective=OBJECTIVE,
        tuner_max_trials=TUNER_MAX_TRIALS,
        study_name=STUDY_NAME,
    )

    vis_callback = PixelVisualizationCallback(val, save_dir="vis/pets/pixel")

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
        train,
        epochs=TRAIN_EPOCHS,
        validation_data=val.cache(),
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

    plot_training_history(history, "Pets Pixel Model Training History")
    print_test_metrics(model, test, "Pets Pixel")
