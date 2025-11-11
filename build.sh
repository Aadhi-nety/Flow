echo "Starting build process..."
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Upgrade pip
pip install --upgrade pip

# Install requirements with specific numpy version first
echo "Installing numpy compatibility version..."
pip install numpy==1.24.3

echo "Installing other requirements..."
pip install -r requirements.txt

echo "Build completed successfully!"
echo "Installed packages:"
pip list
