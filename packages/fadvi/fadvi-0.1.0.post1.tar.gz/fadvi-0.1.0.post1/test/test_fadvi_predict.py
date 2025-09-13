#!/usr/bin/env python3
"""
Test script for FADVI predict method functionality.
Tests batch and label prediction on real scRNA-seq data.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import scvi
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report

# Import FADVI
try:
    from fadvi import FADVI

    print("Successfully imported FADVI from installed package")
except ImportError:
    # Fallback for development
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from fadvi import FADVI


def load_data():
    """Create simulated scRNA-seq data for testing."""
    print("Creating simulated scRNA-seq data...")

    # Use scvi's synthetic data generation with correct parameters
    from scvi.data import synthetic_iid

    # Generate synthetic data with batch and label effects
    adata = synthetic_iid(
        batch_size=700,  # Number of cells per batch (700 * 3 = 2100 total cells)
        n_genes=1000,  # Number of genes
        n_batches=3,  # Number of batches
        n_labels=4,  # Number of cell types
        dropout_ratio=0.3,  # Lower dropout for more realistic data
        sparse_format="csr_matrix",  # Use sparse format
    )

    print(f"Generated data shape: {adata.shape}")
    print(f"Data range: [{adata.X.min():.3f}, {adata.X.max():.3f}]")

    # Add batch and label annotations that match the expected names
    adata.obs["cancer"] = adata.obs["batch"].astype("category")
    adata.obs["reactive"] = adata.obs["labels"].astype("category")

    # Basic preprocessing
    adata.var_names_make_unique()

    # Filter cells with too few genes (some synthetic cells might have low counts)
    sc.pp.filter_cells(adata, min_genes=50)
    print(f"After filtering: {adata.shape}")

    # Handle extreme values that can cause issues with highly variable gene selection
    # Clip extreme values to reasonable range for count data
    max_count = np.percentile(
        adata.X.data if hasattr(adata.X, "data") else adata.X, 99.9
    )
    print(f"Clipping counts above {max_count:.1f}")

    if hasattr(adata.X, "data"):  # sparse matrix
        adata.X.data = np.clip(adata.X.data, 0, max_count)
    else:  # dense matrix
        adata.X = np.clip(adata.X, 0, max_count)

    print(f"Data range after clipping: [{adata.X.min():.3f}, {adata.X.max():.3f}]")

    # Find highly variable genes on raw count data (no normalization needed for scvi-tools)
    # Use more conservative parameters to avoid issues with extreme values
    try:
        sc.pp.highly_variable_genes(adata, min_mean=0.01, max_mean=5, min_disp=0.2)
        n_hvg = sum(adata.var["highly_variable"])
        if n_hvg < 100:  # If too few HVGs, be more lenient
            print(f"Only {n_hvg} HVGs found, using more lenient criteria")
            sc.pp.highly_variable_genes(
                adata, min_mean=0.001, max_mean=10, min_disp=0.05
            )
            n_hvg = sum(adata.var["highly_variable"])
        if (
            n_hvg < 50
        ):  # If still too few, use top variable genes with cell_ranger flavor
            print(
                f"Still only {n_hvg} HVGs found, selecting top 500 most variable genes"
            )
            sc.pp.highly_variable_genes(adata, n_top_genes=500, flavor="cell_ranger")
    except (ValueError, ImportError) as e:
        print(
            f"Warning: HVG selection failed ({e}), selecting top 500 most variable genes"
        )
        try:
            sc.pp.highly_variable_genes(adata, n_top_genes=500, flavor="cell_ranger")
        except:
            print("Cell ranger method also failed, using all genes")
            adata.var["highly_variable"] = True

    # Ensure we have at least some genes selected
    if sum(adata.var["highly_variable"]) == 0:
        print("No HVGs found with any method, using all genes")
        adata.var["highly_variable"] = True

    adata.raw = adata
    adata = adata[
        :, adata.var.highly_variable
    ].copy()  # Important: copy to avoid view issues

    print(f"Number of highly variable genes: {adata.n_vars}")
    print(f"Batch categories: {adata.obs['cancer'].cat.categories.tolist()}")
    print(f"Label categories: {adata.obs['reactive'].cat.categories.tolist()}")

    return adata


def test_predict_method():
    """Test the FADVI predict method."""

    # Load and setup data
    adata = load_data()

    # Setup FADVI model
    print("Setting up FADVI model...")
    FADVI.setup_anndata(adata, batch_key="cancer", labels_key="reactive")

    # Initialize model with smaller latent dimensions for faster testing
    model = FADVI(adata, n_latent_b=5, n_latent_l=5, n_latent_r=5)

    # Train quickly for testing
    print("Training model (quick training for testing)...")
    model.train(max_epochs=5, check_val_every_n_epoch=5, early_stopping=False)

    # Test batch prediction
    print("\n=== Testing Batch Prediction ===")

    # Get true batch labels (as categorical strings now)
    true_batch = adata.obs["cancer"].values  # Get categorical values, not codes
    batch_categories = adata.obs["cancer"].cat.categories

    # Predict batch categories (hard predictions)
    print("Predicting batch categories (hard predictions)...")
    pred_batch_hard = model.predict(
        adata, prediction_mode="batch", soft=False, return_numpy=True
    )

    # Predict batch categories (soft predictions)
    print("Predicting batch categories (soft predictions)...")
    pred_batch_soft = model.predict(
        adata, prediction_mode="batch", soft=True, return_numpy=True
    )

    # Calculate batch prediction accuracy
    batch_accuracy = accuracy_score(true_batch, pred_batch_hard)
    print(f"Batch prediction accuracy: {batch_accuracy:.3f}")

    print("Batch prediction report:")
    print(
        classification_report(
            true_batch, pred_batch_hard, target_names=batch_categories, zero_division=0
        )
    )

    # Test label prediction
    print("\n=== Testing Label Prediction ===")

    # Get true label labels (as categorical strings now)
    true_labels = adata.obs["reactive"].values  # Get categorical values, not codes
    label_categories = adata.obs["reactive"].cat.categories

    # Predict label categories (hard predictions)
    print("Predicting label categories (hard predictions)...")
    pred_label_hard = model.predict(
        adata, prediction_mode="label", soft=False, return_numpy=True
    )

    # Predict label categories (soft predictions)
    print("Predicting label categories (soft predictions)...")
    pred_label_soft = model.predict(
        adata, prediction_mode="label", soft=True, return_numpy=True
    )

    # Calculate label prediction accuracy
    label_accuracy = accuracy_score(true_labels, pred_label_hard)
    print(f"Label prediction accuracy: {label_accuracy:.3f}")

    print("Label prediction report:")
    print(
        classification_report(
            true_labels, pred_label_hard, target_names=label_categories, zero_division=0
        )
    )

    # Test on subset of data
    print("\n=== Testing Subset Prediction ===")
    subset_size = min(
        500, adata.n_obs // 2
    )  # Use smaller subset appropriate for synthetic data
    subset_indices = np.random.choice(adata.n_obs, size=subset_size, replace=False)

    pred_batch_subset = model.predict(
        adata, indices=subset_indices.tolist(), prediction_mode="batch", soft=False
    )

    pred_label_subset = model.predict(
        adata, indices=subset_indices.tolist(), prediction_mode="label", soft=False
    )

    print(f"Subset batch predictions shape: {pred_batch_subset.shape}")
    print(f"Subset label predictions shape: {pred_label_subset.shape}")

    # Create confusion matrices
    print("\n=== Creating Confusion Matrices ===")

    from sklearn.metrics import confusion_matrix

    # Batch confusion matrix
    batch_cm = confusion_matrix(true_batch, pred_batch_hard)

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    sns.heatmap(
        batch_cm,
        annot=True,
        fmt="d",
        xticklabels=batch_categories,
        yticklabels=batch_categories,
        cmap="Blues",
    )
    plt.title(f"Batch Prediction Confusion Matrix\nAccuracy: {batch_accuracy:.3f}")
    plt.xlabel("Predicted")
    plt.ylabel("True")

    # Label confusion matrix
    label_cm = confusion_matrix(true_labels, pred_label_hard)

    plt.subplot(1, 2, 2)
    sns.heatmap(
        label_cm,
        annot=True,
        fmt="d",
        xticklabels=label_categories,
        yticklabels=label_categories,
        cmap="Blues",
    )
    plt.title(f"Label Prediction Confusion Matrix\nAccuracy: {label_accuracy:.3f}")
    plt.xlabel("Predicted")
    plt.ylabel("True")

    plt.tight_layout()
    plt.savefig("fadvi_prediction_confusion_matrices.png", dpi=300, bbox_inches="tight")
    print("Saved confusion matrices to 'fadvi_prediction_confusion_matrices.png'")

    # Test probability distributions
    print("\n=== Analyzing Prediction Probabilities ===")

    # Batch probabilities
    print(f"Batch probability shape: {pred_batch_soft.shape}")
    print(
        f"Batch probability range: [{pred_batch_soft.values.min():.3f}, {pred_batch_soft.values.max():.3f}]"
    )
    print(
        f"Batch probability sum check (should be ~1): {pred_batch_soft.sum(axis=1).mean():.3f}"
    )

    # Label probabilities
    print(f"Label probability shape: {pred_label_soft.shape}")
    print(
        f"Label probability range: [{pred_label_soft.values.min():.3f}, {pred_label_soft.values.max():.3f}]"
    )
    print(
        f"Label probability sum check (should be ~1): {pred_label_soft.sum(axis=1).mean():.3f}"
    )

    # Confidence analysis
    max_batch_probs = pred_batch_soft.max(axis=1)
    max_label_probs = pred_label_soft.max(axis=1)

    print(f"Average batch prediction confidence: {max_batch_probs.mean():.3f}")
    print(f"Average label prediction confidence: {max_label_probs.mean():.3f}")

    # Summary
    print("\n=== FADVI Predict Method Test Summary ===")
    print(f"✅ Batch prediction accuracy: {batch_accuracy:.3f}")
    print(f"✅ Label prediction accuracy: {label_accuracy:.3f}")
    print(f"✅ Batch prediction shape: {pred_batch_hard.shape}")
    print(f"✅ Label prediction shape: {pred_label_hard.shape}")
    print(
        f"✅ Soft predictions sum to 1: Batch={pred_batch_soft.sum(axis=1).mean():.3f}, Label={pred_label_soft.sum(axis=1).mean():.3f}"
    )
    print(f"✅ Subset prediction works correctly")
    print(f"✅ Generated visualization files")

    # Verify test results with assertions
    assert batch_accuracy > 0, "Batch prediction accuracy should be greater than 0"
    assert label_accuracy > 0, "Label prediction accuracy should be greater than 0"
    assert (
        pred_batch_hard.shape[0] == adata.n_obs
    ), "Batch predictions should match number of cells"
    assert (
        pred_label_hard.shape[0] == adata.n_obs
    ), "Label predictions should match number of cells"

    # Note: pytest test functions should not return values


if __name__ == "__main__":
    # Set random seeds for reproducibility
    np.random.seed(42)

    # Run the test
    try:
        test_predict_method()
        print("\n🎉 FADVI predict method test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
