from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np
import editdistance  # pip install editdistance

def compute_metrics(pred):
    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad_token_id
    label_ids[label_ids == -100] = tokenizer.pad_token_id

    # Decode
    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    # Split into tokens (word-level) 
    pred_tokens = [s.split() for s in pred_str]
    label_tokens = [s.split() for s in label_str]

    # Token Accuracy
    total_tokens, correct_tokens = 0, 0
    y_true, y_pred = [], []  # for precision/recall/f1

    for preds, labels in zip(pred_tokens, label_tokens):
        for p, l in zip(preds, labels):
            y_true.append(l)
            y_pred.append(p)
            if p == l:
                correct_tokens += 1
            total_tokens += 1

    token_accuracy = correct_tokens / total_tokens if total_tokens > 0 else 0.0

    # Sentence Accuracy (Exact Match)
    correct_sentences = sum([p == l for p, l in zip(pred_str, label_str)])
    sentence_accuracy = correct_sentences / len(label_str)

    # Precision / Recall / F1 (macro avg)
    precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    # Character Accuracy
    total_chars, correct_chars = 0, 0
    for p, l in zip(pred_str, label_str):
        min_len = min(len(p), len(l))
        for i in range(min_len):
            if p[i] == l[i]:
                correct_chars += 1
        total_chars += max(len(p), len(l))
    char_accuracy = correct_chars / total_chars if total_chars > 0 else 0.0

    # Edit Distance based Accuracy
    total_edit, total_len = 0, 0
    for p, l in zip(pred_str, label_str):
        total_edit += editdistance.eval(p.split(), l.split())
        total_len += max(len(p.split()), len(l.split()))
    edit_distance_acc = 1 - (total_edit / total_len) if total_len > 0 else 0.0

    return {
        "token_accuracy": token_accuracy * 100,
        "sentence_accuracy": sentence_accuracy * 100,
        "precision": precision * 100,
        "recall": recall * 100,
        "f1": f1 * 100,
        "char_accuracy": char_accuracy * 100,
        "edit_distance_acc": edit_distance_acc * 100,
        "total_tokens": total_tokens,
        "correct_tokens": correct_tokens,
    }
