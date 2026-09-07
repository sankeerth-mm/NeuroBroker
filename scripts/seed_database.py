import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app.database import AsyncSessionLocal, init_db
from backend.app.models.user import User
from backend.app.models.model_pkg import ModelPackage
from backend.app.models.dataset import Dataset
from backend.app.security.hashing import get_password_hash
from backend.app.security.checksum import compute_sha256
from backend.app.config import BASE_DIR
from sqlalchemy import select

async def seed():
    print("Initializing database tables...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 1. Seed Admin & Demo User
        admin_res = await db.execute(select(User).where(User.email == "admin@neurobroker.org"))
        admin = admin_res.scalars().first()
        if not admin:
            admin = User(
                name="Cluster Administrator",
                email="admin@neurobroker.org",
                password_hash=get_password_hash("AdminPassword123!"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            await db.flush()
            print("Created default Admin user: admin@neurobroker.org / AdminPassword123!")
            
        user_res = await db.execute(select(User).where(User.email == "user@neurobroker.org"))
        normal_user = user_res.scalars().first()
        if not normal_user:
            normal_user = User(
                name="Demo Researcher",
                email="user@neurobroker.org",
                password_hash=get_password_hash("AdminPassword123!"),
                role="user",
                is_active=True
            )
            db.add(normal_user)
            await db.flush()
            print("Created default Demo user: user@neurobroker.org / AdminPassword123!")
            
        # 2. Seed Example Model Package
        model_zip = BASE_DIR / "example_models" / "mnist_cnn_package.zip"
        if model_zip.exists():
            m_res = await db.execute(select(ModelPackage).where(ModelPackage.name == "MNIST_CNN_Classifier"))
            if not m_res.scalars().first():
                pkg = ModelPackage(
                    user_id=admin.id,
                    name="MNIST_CNN_Classifier",
                    description="Standard Convolutional Neural Network for digit classification with 2 conv layers and dropout",
                    framework="pytorch",
                    file_path=str(model_zip),
                    config_json={"input_shape": [1, 28, 28], "num_classes": 10, "default_lr": 0.01},
                    checksum_sha256=compute_sha256(model_zip),
                    is_validated=True
                )
                db.add(pkg)
                print("Seeded default model package: MNIST_CNN_Classifier")
                
        # 3. Seed Example Datasets
        mnist_zip = BASE_DIR / "example_datasets" / "mnist_sample_dataset.zip"
        if mnist_zip.exists():
            d_res = await db.execute(select(Dataset).where(Dataset.name == "MNIST Sample Dataset"))
            if not d_res.scalars().first():
                ds = Dataset(
                    user_id=admin.id,
                    name="MNIST Sample Dataset",
                    description="Balanced 10-class handwritten digit dataset (600 samples)",
                    dataset_type="image_classification",
                    file_path=str(mnist_zip),
                    total_samples=600,
                    total_size_bytes=mnist_zip.stat().st_size,
                    class_distribution={str(i): 60 for i in range(10)},
                    checksum_sha256=compute_sha256(mnist_zip),
                    is_validated=True,
                    is_non_iid=False
                )
                db.add(ds)
                print("Seeded default dataset: MNIST Sample Dataset")
                
        csv_file = BASE_DIR / "example_datasets" / "synthetic_tabular.csv"
        if csv_file.exists():
            d_res2 = await db.execute(select(Dataset).where(Dataset.name == "Synthetic Tabular Dataset"))
            if not d_res2.scalars().first():
                ds2 = Dataset(
                    user_id=admin.id,
                    name="Synthetic Tabular Dataset",
                    description="Multi-class tabular dataset (600 rows, 4 features)",
                    dataset_type="csv_classification",
                    file_path=str(csv_file),
                    total_samples=600,
                    total_size_bytes=csv_file.stat().st_size,
                    class_distribution={"0": 200, "1": 200, "2": 200},
                    label_column="label",
                    checksum_sha256=compute_sha256(csv_file),
                    is_validated=True,
                    is_non_iid=False
                )
                db.add(ds2)
                print("Seeded default dataset: Synthetic Tabular Dataset")
                
        await db.commit()
        print("\nDatabase successfully seeded!")

if __name__ == "__main__":
    asyncio.run(seed())
