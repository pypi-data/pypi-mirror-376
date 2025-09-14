"""
PySwissLib - A comprehensive utility library for Python
Author: Gautham Nair
Version: 1.0.1

Installation requirements:
pip install numpy pandas matplotlib seaborn torch scikit-learn requests
"""

import os
import sys
import platform
import subprocess
import importlib.util
import logging
import json
from typing import List, Any, Dict, Optional, Union
from functools import lru_cache
import re

# Configure centralized logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PySwissLib')

# Define custom exceptions
class PySwissLibError(Exception):
    """Base exception for PySwissLib errors."""
    pass

class DependencyError(PySwissLibError):
    """Exception raised for missing dependencies."""
    pass

class ConfigError(PySwissLibError):
    """Exception raised for configuration issues."""
    pass

class ModelError(PySwissLibError):
    """Exception raised for model-related issues."""
    pass

# Dependency checker and installer
def check_and_install_dependencies() -> bool:
    """Check for required dependencies and install if missing."""
    required_packages: Dict[str, str] = {
        'numpy': 'numpy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'requests': 'requests',
        'torch': 'torch',
        'sklearn': 'scikit-learn'
    }

    missing_packages: List[str] = []

    for package_name, pip_name in required_packages.items():
        if importlib.util.find_spec(package_name) is None:
            missing_packages.append(pip_name)

    if missing_packages:
        logger.warning(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Attempting to install dependencies...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', *missing_packages
            ])
            logger.info("Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            logger.error("Please install manually or use a virtual environment.")
            return False
    return True

# Check for dependencies, but do not import them globally
DEPENDENCIES_AVAILABLE = check_and_install_dependencies()

class Basic:
    """General system and utility functions."""
    @staticmethod
    def sys_identify() -> str:
        """Identify the operating system."""
        system = platform.system()
        if system == "Windows":
            return "Windows"
        elif system == "Darwin":
            return "macOS"
        elif system == "Linux":
            return "Linux"
        else:
            return f"Unix-like ({system})"

    @staticmethod
    def clrscr() -> None:
        """Clear the screen."""
        if sys.platform == "win32":
            os.system('cls')
        else:
            os.system('clear')

    @staticmethod
    def get_python_version() -> platform.python_version_tuple:
        """Get Python version info."""
        return sys.version_info

    @staticmethod
    def get_platform_info() -> Dict[str, str]:
        """Get detailed platform information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }

    @staticmethod
    def install_package(package_name: str) -> bool:
        """Install a Python package using pip."""
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
            return True
        except subprocess.CalledProcessError:
            return False

class String:
    """String manipulation utilities."""
    @staticmethod
    def strcmp(str1: str, str2: str, case_sensitive: bool = True) -> bool:
        """Compare two strings."""
        if not case_sensitive:
            return str1.lower() == str2.lower()
        return str1 == str2

    @staticmethod
    def strcount(string: str) -> int:
        """Count characters in a string."""
        return len(string)

    @staticmethod
    def word_count(string: str) -> int:
        """Count words in a string."""
        return len(string.split())

    @staticmethod
    def reverse_string(string: str) -> str:
        """Reverse a string."""
        return string[::-1]

    @staticmethod
    def is_palindrome(string: str) -> bool:
        """Check if string is a palindrome."""
        clean = string.lower().replace(' ', '')
        return clean == clean[::-1]

    @staticmethod
    def capitalize_words(string: str) -> str:
        """Capitalize first letter of each word."""
        return string.title()

    @staticmethod
    def extract_numbers(string: str) -> List[int]:
        """Extract all numbers from a string."""
        return [int(x) for x in re.findall(r'\d+', string)]

    @staticmethod
    def remove_special_chars(string: str, keep_spaces: bool = True) -> str:
        """Remove special characters from string."""
        if keep_spaces:
            return re.sub(r'[^a-zA-Z0-9\s]', '', string)
        else:
            return re.sub(r'[^a-zA-Z0-9]', '', string)

class Math:
    """Mathematical operations and utilities."""
    @staticmethod
    def factorial(n: int) -> int:
        """Calculate factorial of a number."""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers.")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    @staticmethod
    def is_prime(n: int) -> bool:
        """Check if a number is prime."""
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def fibonacci(n: int) -> List[int]:
        """Generate fibonacci sequence up to n terms."""
        if n <= 0:
            return []
        if n == 1:
            return [0]
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[i-1] + fib[i-2])
        return fib

    @staticmethod
    def gcd(a: int, b: int) -> int:
        """Find Greatest Common Divisor."""
        while b:
            a, b = b, a % b
        return a

    @staticmethod
    def lcm(a: int, b: int) -> int:
        """Find Least Common Multiple."""
        if a == 0 or b == 0:
            return 0
        return abs(a * b) // Math.gcd(a, b)

class DataScience:
    """Data science utilities using numpy, pandas, matplotlib."""

    @staticmethod
    def create_dataframe(data: Optional[Any] = None, columns: Optional[List[str]] = None) -> Optional[Any]:
        """Create a pandas DataFrame."""
        try:
            import pandas as pd
            return pd.DataFrame(data, columns=columns)
        except ImportError:
            raise DependencyError("Pandas not available. Please install it.")

    @staticmethod
    def read_csv(filepath: str, **kwargs) -> Optional[Any]:
        """Read CSV file into DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise DependencyError("Pandas not available. Please install it.")
        try:
            return pd.read_csv(filepath, **kwargs)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return None

    @staticmethod
    def basic_stats(dataframe: Any, column: Optional[str] = None) -> Optional[Any]:
        """Get basic statistics of dataframe or column."""
        try:
            import pandas as pd
        except ImportError:
            raise DependencyError("Pandas not available. Please install it.")

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if column:
            if column not in dataframe.columns:
                raise ValueError(f"Column '{column}' not found in DataFrame.")
            return dataframe[column].describe()
        return dataframe.describe()

    @staticmethod
    def create_array(data: Any, dtype: Optional[str] = None) -> Optional[Any]:
        """Create numpy array."""
        try:
            import numpy as np
            return np.array(data, dtype=dtype)
        except ImportError:
            raise DependencyError("Numpy not available. Please install it.")

    @staticmethod
    def array_stats(array: Any) -> Dict[str, float]:
        """Get statistics of numpy array."""
        try:
            import numpy as np
        except ImportError:
            raise DependencyError("Numpy not available. Please install it.")

        if not isinstance(array, np.ndarray):
            raise TypeError("Input must be a numpy array.")

        return {
            'mean': float(np.mean(array)),
            'median': float(np.median(array)),
            'std': float(np.std(array)),
            'min': float(np.min(array)),
            'max': float(np.max(array)),
            'sum': float(np.sum(array))
        }

    @staticmethod
    def correlation_matrix(dataframe: Any) -> Optional[Any]:
        """Calculate correlation matrix."""
        try:
            import pandas as pd
        except ImportError:
            raise DependencyError("Pandas not available. Please install it.")

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        return dataframe.corr(numeric_only=True)

class Visualization:
    """Data visualization utilities."""
    @staticmethod
    def line_plot(x: Any, y: Any, title: str = "Line Plot", xlabel: str = "X", ylabel: str = "Y", figsize: tuple = (10, 6)) -> None:
        """Create a line plot."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise DependencyError("Matplotlib not available. Please install it.")

        plt.figure(figsize=figsize)
        plt.plot(x, y)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.show()

    @staticmethod
    def bar_plot(x: Any, y: Any, title: str = "Bar Plot", xlabel: str = "X", ylabel: str = "Y", figsize: tuple = (10, 6)) -> None:
        """Create a bar plot."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise DependencyError("Matplotlib not available. Please install it.")

        plt.figure(figsize=figsize)
        plt.bar(x, y)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()

    @staticmethod
    def histogram(data: Any, bins: int = 30, title: str = "Histogram", xlabel: str = "Value", ylabel: str = "Frequency", figsize: tuple = (10, 6)) -> None:
        """Create a histogram."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise DependencyError("Matplotlib not available. Please install it.")

        plt.figure(figsize=figsize)
        plt.hist(data, bins=bins, alpha=0.7, edgecolor='black')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()

    @staticmethod
    def scatter_plot(x: Any, y: Any, title: str = "Scatter Plot", xlabel: str = "X", ylabel: str = "Y", figsize: tuple = (10, 6)) -> None:
        """Create a scatter plot."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise DependencyError("Matplotlib not available. Please install it.")

        plt.figure(figsize=figsize)
        plt.scatter(x, y, alpha=0.7)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True, alpha=0.3)
        plt.show()

    @staticmethod
    def heatmap(data: Any, title: str = "Heatmap", figsize: tuple = (10, 8)) -> None:
        """Create a heatmap."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError:
            raise DependencyError("Matplotlib or Seaborn not available. Please install them.")

        plt.figure(figsize=figsize)
        sns.heatmap(data, annot=True, cmap='viridis')
        plt.title(title)
        plt.show()

class FileHandler:
    """File operations utilities."""
    @staticmethod
    def read_file(filepath: str, mode: str = 'r', encoding: str = 'utf-8') -> Optional[str]:
        """Read file content."""
        try:
            with open(filepath, mode, encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Error: The file at {filepath} was not found.")
            return None
        except IOError as e:
            logger.error(f"Error reading file: {e}")
            return None

    @staticmethod
    def write_file(filepath: str, content: str, mode: str = 'w', encoding: str = 'utf-8') -> bool:
        """Write content to file."""
        try:
            with open(filepath, mode, encoding=encoding) as f:
                f.write(content)
            return True
        except IOError as e:
            logger.error(f"Error writing file: {e}")
            return False

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if file exists."""
        return os.path.exists(filepath)

    @staticmethod
    def create_directory(dirpath: str) -> bool:
        """Create directory if it doesn't exist."""
        try:
            os.makedirs(dirpath, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory: {e}")
            return False

    @staticmethod
    def list_files(directory: str, extension: Optional[str] = None) -> List[str]:
        """List files in directory."""
        try:
            files = os.listdir(directory)
            if extension:
                files = [f for f in files if f.endswith(extension)]
            return files
        except FileNotFoundError:
            logger.error(f"Error: The directory at {directory} was not found.")
            return []

class Network:
    """Network utilities."""
    @staticmethod
    def ping(host: str) -> bool:
        """Ping a host."""
        try:
            ping_cmd = ['ping', '-n', '1'] if platform.system().lower() == "windows" else ['ping', '-c', '1']
            result = subprocess.run(ping_cmd + [host], capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Ping failed for host {host}: {e}")
            return False

    @staticmethod
    @lru_cache(maxsize=128)
    def get_json(url: str) -> Optional[Dict]:
        """Get JSON data from a URL with caching."""
        try:
            import requests
        except ImportError:
            raise DependencyError("Requests not available. Please install it.")

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            return None

class Config:
    """Configuration management utility."""
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self._config = {}
        self.load()

    def load(self) -> None:
        """Load configuration from a JSON file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
            except (IOError, json.JSONDecodeError) as e:
                raise ConfigError(f"Failed to load configuration file: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def save(self) -> None:
        """Save current configuration to the JSON file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except IOError as e:
            logger.error(f"Failed to save configuration file: {e}")

class AI_ML:
    """AI and Machine Learning utilities using PyTorch."""
    @staticmethod
    def get_device() -> Any:
        """Get the available torch device (GPU or CPU)."""
        try:
            import torch
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {device}")
            return device
        except ImportError:
            raise DependencyError("PyTorch not available. Please install it.")

    @staticmethod
    def train_model(model: Any, data_loader: Any,
                    optimizer: Any, criterion: Any,
                    epochs: int = 10, device: Optional[Any] = None) -> None:
        """A simple training loop for a PyTorch model."""
        try:
            import torch
        except ImportError:
            raise DependencyError("PyTorch not available. Please install it.")

        if device is None:
            device = AI_ML.get_device()

        model.to(device)
        model.train()

        for epoch in range(epochs):
            total_loss = 0
            for inputs, labels in data_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(data_loader):.4f}")

    @staticmethod
    def evaluate_model(model: Any, data_loader: Any,
                       device: Optional[Any] = None) -> float:
        """Evaluate a PyTorch model's accuracy."""
        try:
            import torch
        except ImportError:
            raise DependencyError("PyTorch not available. Please install it.")

        if device is None:
            device = AI_ML.get_device()

        model.to(device)
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in data_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        accuracy = 100 * correct / total
        logger.info(f"Accuracy on test data: {accuracy:.2f}%")
        return accuracy

# Convenience function to check library status
def library_status() -> Dict[str, Any]:
    """Check the status of PySwissLib."""
    status = {
        'Python Version': platform.python_version(),
        'Platform': platform.system(),
        'Dependencies Available': DEPENDENCIES_AVAILABLE,
        'Available Modules': [
            'Basic', 'String', 'Math', 'FileHandler', 'Network', 'Config'
        ]
    }

    if DEPENDENCIES_AVAILABLE:
        status['Available Modules'].extend(['DataScience', 'Visualization', 'AI_ML'])

    return status

if __name__ == "__main__":
    logger.info("Starting PySwissLib Example Usage")

    print("=== PySwissLib Status ===")
    for key, value in library_status().items():
        print(f"{key}: {value}")

    if DEPENDENCIES_AVAILABLE:
        try:
            import numpy as np
            import pandas as pd
            import torch
            from sklearn.model_selection import train_test_split

            print("\n=== AI/ML Tests ===")
            # 1. Prepare sample data for a simple classification task
            from sklearn.datasets import make_classification
            X, y = make_classification(n_samples=1000, n_features=20, n_classes=2, random_state=42)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Convert to PyTorch tensors and create data loaders
            train_data = torch.utils.data.TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
            test_data = torch.utils.data.TensorDataset(torch.tensor(X_test, dtype=torch.float32), torch.tensor(y_test, dtype=torch.long))
            train_loader = torch.utils.data.DataLoader(train_data, batch_size=32, shuffle=True)
            test_loader = torch.utils.data.DataLoader(test_data, batch_size=32, shuffle=False)

            # 2. Define a simple PyTorch model
            class SimpleNet(torch.nn.Module):
                def __init__(self, input_dim):
                    super(SimpleNet, self).__init__()
                    self.layer = torch.nn.Sequential(
                        torch.nn.Linear(input_dim, 64),
                        torch.nn.ReLU(),
                        torch.nn.Linear(64, 2)
                    )

                def forward(self, x):
                    return self.layer(x)

            # 3. Use AI_ML class to train and evaluate the model
            try:
                device = AI_ML.get_device()
                model = SimpleNet(input_dim=20).to(device)
                criterion = torch.nn.CrossEntropyLoss()
                optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

                print("\nStarting model training...")
                AI_ML.train_model(model, train_loader, optimizer, criterion, epochs=5)

                print("\nEvaluating model...")
                AI_ML.evaluate_model(model, test_loader)
            except DependencyError as e:
                logger.error(e)

        except ImportError:
            print("\n=== AI/ML Features Unavailable due to missing dependencies ===")
            print("Please ensure you have run 'pip install numpy pandas matplotlib seaborn torch scikit-learn requests' in a virtual environment.")

    else:
        print("\n=== AI/ML Features Unavailable ===")
        print("Please ensure you have run 'pip install numpy pandas matplotlib seaborn torch scikit-learn requests' in a virtual environment.")
