import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from sklearn.calibration import CalibrationDisplay
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    roc_auc_score, 
    precision_recall_curve, 
    auc, 
    f1_score,
    precision_score,
    recall_score,
    matthews_corrcoef,
    brier_score_loss,
    PrecisionRecallDisplay,
    RocCurveDisplay,
    confusion_matrix
)


class QualityMetrics:
    def __init__(self, y_test: np.array, y_pred: np.array, y_scores: np.array, unique_id: np.array) -> None:
        self.y_test = y_test
        self.y_pred = y_pred
        self.y_scores = y_scores
        self.unique_id = unique_id
    
    def get_metrics(self) -> pd.DataFrame:
        y_prop = self.y_test.mean()
        n_test = len(self.y_test)
        roc_auc = roc_auc_score(self.y_test, self.y_scores)

        precision_list,recall_list,_ = precision_recall_curve(self.y_test, self.y_scores)
        pr_auc = auc(recall_list, precision_list)
        
        f1 = f1_score(self.y_test, self.y_pred)
        precision = precision_score(self.y_test, self.y_pred)
        recall = recall_score(self.y_test, self.y_pred)
        mcc = matthews_corrcoef(self.y_test, self.y_pred)
        brier_score = brier_score_loss(self.y_test, self.y_scores)
        brier_score_w = weighted_brier_score(self.y_test, self.y_scores)
        ece = get_ece(self.y_test, self.y_scores)
        spe = get_best_spe(self.y_test, self.y_scores, self.unique_id)
        return pd.DataFrame(
            {
                "train_y_prop":y_prop,
                "test_n":n_test,
                "f1":f1,
                "precision":precision,
                "recall":recall,
                "roc_auc":roc_auc,
                "pr_auc":pr_auc,
                "mcc":mcc,
                "brier_score":brier_score,
                "brier_score_w":brier_score_w,
                "ece":ece,
                "spe":spe,
                
            }
        , index=[0]
        )


def fpr_score(y_true, y_pred, neg_label=0, pos_label=1):
    cm = confusion_matrix(y_true, y_pred, labels=[neg_label, pos_label])
    tn, fp, _, _ = cm.ravel()
    tnr = tn / (tn + fp)
    return 1 - tnr


def pr_roc_plots_lc(df, vertical=None, pos_label=1, neg_label=0):
    for logical_category in tqdm(df.query(f'vertical == "{vertical}"').logical_category.unique()):
        data = df.query(f'logical_category == "{logical_category}"')
        # Create subplots pattern
        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(14, 6))
        # Plot PR-AUC
        PrecisionRecallDisplay.from_predictions(data.y_test, data.pred_proba, pos_label=pos_label, ax=axs[0], name="Vanilla_LogReg")
        axs[0].plot(
            recall_score(y_true=data.y_test, y_pred=data.y_pred),
            precision_score(y_true=data.y_test, y_pred=data.y_pred),
            marker="o",
            markersize=10,
            color="tab:blue",
            label="Default cut-off point at a probability of 0.5",
        )
        axs[0].set_title("Precision-Recall curve")
        axs[0].legend()
        # Plot ROC-AUC
        RocCurveDisplay.from_predictions(data.y_test, data.pred_proba, pos_label=pos_label, ax=axs[1], name="Vanilla_LogReg", plot_chance_level=True)
        axs[1].plot(
            fpr_score(y_true=data.y_test, y_pred=data.y_pred),
            recall_score(y_true=data.y_test, y_pred=data.y_pred),
            marker="o",
            markersize=10,
            color="tab:blue",
            label="Default cut-off point at a probability of 0.5",
        )
        axs[1].set_title("ROC curve")
        axs[1].legend()
        _ = fig.suptitle(f'{logical_category}')


def pr_roc_plots_v(df, pos_label=1, neg_label=0):
    for vertical in tqdm(df.vertical.unique()):  
        data = df.query(f'vertical == "{vertical}"')
        # Create subplots pattern
        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(14, 6))
        # Plot PR-AUC
        PrecisionRecallDisplay.from_predictions(data.y_test, data.pred_proba, pos_label=pos_label, ax=axs[0], name="Vanilla_LogReg")
        axs[0].plot(
            recall_score(y_true=data.y_test, y_pred=data.y_pred),
            precision_score(y_true=data.y_test, y_pred=data.y_pred),
            marker="o",
            markersize=10,
            color="tab:blue",
            label="Default cut-off point at a probability of 0.5",
        )
        axs[0].set_title("Precision-Recall curve")
        axs[0].legend()
        # Plot ROC-AUC
        RocCurveDisplay.from_predictions(data.y_test, data.pred_proba, pos_label=pos_label, ax=axs[1], name="Vanilla_LogReg", plot_chance_level=True)
        axs[1].plot(
            fpr_score(y_true=data.y_test, y_pred=data.y_pred),
            recall_score(y_true=data.y_test, y_pred=data.y_pred),
            marker="o",
            markersize=10,
            color="tab:blue",
            label="Default cut-off point at a probability of 0.5",
        )
        axs[1].set_title("ROC curve")
        axs[1].legend()
        _ = fig.suptitle(f'{vertical}')


def weighted_brier_score(y_true, y_pred_proba):
    unique_weights = compute_class_weight(class_weight="balanced", classes=np.unique(y_true), y=y_true)
    func = np.vectorize(lambda x: unique_weights[x]) 
    weights = func(y_true)
    return np.sum(weights * (y_pred_proba - y_true) ** 2) / np.sum(weights)


def get_best_spe(y_test, predict_propba, unique_id):
    sorted_indexes = np.lexsort((unique_id, predict_propba))
    y = y_test[sorted_indexes]
    pp = predict_propba[sorted_indexes]
    spe = abs(pp.cumsum() - y.cumsum()).sum() 
    norm_spe = spe / len(y_test) / max(1, y.sum())
    return norm_spe


def give_ece_data(preds,bins,y_valid):
    sorted_ind = np.argsort(preds)
    predicted_bins = [[] for _ in range(bins)]
    actual_counters = [[] for _ in range(bins)]
    counters = [[] for _ in range(bins)]
    index = 0
    length_array = len(sorted_ind)
    step = 1.*length_array//bins
    for _ in range(bins):
        current = int(step*index)
        next_ = int(step*(index+1))
        predicted_bins[index] = np.mean(preds[sorted_ind[current:next_]])
        actual_counters[index] = np.mean(y_valid[sorted_ind[current:next_]])
        counters[index] = len(y_valid[sorted_ind[current:next_]])
        index += 1
    return predicted_bins,actual_counters,counters


def get_ece(y_test, pred_proba, bins=10):
    # source 1: https://www.youtube.com/watch?v=IL7sWMOazXQ
    # source 2: https://drive.google.com/drive/folders/1avFRIC03khCjcmI0SyxzsjusSWk23Asi
    predicted_bins,actual_counters,counters = give_ece_data(pred_proba, bins, y_test)
    ece = 0
    for j in range(bins):
        ece +=  counters[j]*np.abs((predicted_bins[j] - actual_counters[j]))
    ece /= len(pred_proba)

    return ece


def ece_plot(y_val, clf_list, lc_name):
    fig, ax = plt.subplots()
    colors = plt.get_cmap("Dark2")

    calibration_displays = {}
    markers = ["^", "v", "s", "o"]
    for i, (prob, name) in enumerate(clf_list):    
        calibration_displays[name] = CalibrationDisplay.from_predictions(
            y_val, 
            prob,
            n_bins=10,
            ax=ax,
            name=name,
            color=colors(i),
            marker=markers[i],
            strategy='uniform'
        )
    plt.title(lc_name)
    plt.show()