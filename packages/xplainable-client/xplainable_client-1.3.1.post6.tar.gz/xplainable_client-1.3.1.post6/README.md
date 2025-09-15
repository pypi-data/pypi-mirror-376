
<div align="center">
<img src="https://raw.githubusercontent.com/xplainable/xplainable/main/docs/assets/logo/xplainable-logo.png">
<h1 align="center">xplainable</h1>
<h3 align="center">Real-time explainable machine learning for business optimisation</h3>
    
**Xplainable** makes tabular machine learning transparent, fair, and actionable.
</div>

## Why Was Xplainable Created?
In machine learning, there has long been a trade-off between accuracy and explainability. This drawback has led to the creation of explainable ML libraries such as [Shap](https://github.com/slundberg/shap) and [Lime](https://github.com/marcotcr/lime) which make estimations of model decision processes. These can be incredibly time-expensive and often present steep learning curves making them challenging to implement effectively in production environments.

To solve this problem, we created `xplainable`. **xplainable** presents a suite of novel machine learning algorithms specifically designed to match the performance of popular black box models like [XGBoost](https://github.com/dmlc/xgboost) and [LightGBM](https://github.com/microsoft/LightGBM) while providing complete transparency, all in real-time.


## Xplainable Cloud
This Python package is free and open-source. To add more value to data teams within organisations, we also created Xplainable Cloud that brings your models to a collaborative environment.

### Preprocessing with Xplainable Cloud
Before modeling, it's essential to preprocess your data. Xplainable Cloud facilitates this process by allowing you to create and manage preprocessors in the cloud.


```python
import xplainable as xp
import os
from xplainable_client.client import Client

# Initialising the client
client = Client(api_key=os.environ['XP_API_KEY'])

# Creating a Preprocessor (creates both ID and version)
preprocessor_id, version_id = client.preprocessing.create_preprocessor(
    preprocessor_name="Preprocessor Name",
    preprocessor_description="Preprocessor Description",
    pipeline=pipeline,  # <-- Pass the pipeline
    df=df  # <-- Pass the raw dataframe
)

# Loading the Preprocessor Client
pp_cloud = client.preprocessing.load_preprocessor(
    preprocessor_id,
    version_id,
)
```

### Modelling with Xplainable Cloud

After preprocessing, the next step is to create and train your model. Xplainable Cloud supports model versioning and ID creation to streamline this process.

```python

# Creating a Model (creates both ID and version)
model_id, version_id = client.models.create_model(
    model=model,
    model_name="Model Name",
    model_description='Model Description',
    x=X_train,
    y=y_train
)

```

### Deployments with Xplainable Cloud
Once your model is ready, deploying it is straightforward with Xplainable Cloud. You can deploy, activate, and manage API keys for your model deployment keys within your IDE or environment.

```python 
# Creating a Model Deployment
deployment = client.deployments.deploy(model_version_id=version_id)

# Activating the Deployment
client.deployments.activate_deployment(deployment.deployment_id)

# Generating an API Key
deploy_key = client.deployments.create_deployment_key(
    deployment_id=deployment.deployment_id,
    description='API Key Name',
    expiry_days=7  # Days until expiration
)

# Hitting the endpoint
response = requests.post(
    url="https://inference.xplainable.io/v1/predict",
    headers={'api_key': deploy_key.deploy_key},
    json=body
)

# Obtaining the value response
value = response.json()
```

## Release Process

The xplainable-client uses automated release scripts to streamline version management and integrate with the [Xplainable MCP Server](https://github.com/jtuppack/xplainable-mcp-server).

### Creating a New Release

Use the automated release scripts in the `scripts/` directory:

```bash
# Quick patch release (1.2.3 → 1.2.4)
./scripts/release.sh --increment patch

# Minor release with new features (1.2.3 → 1.3.0)
./scripts/release.sh --increment minor

# Major release with breaking changes (1.2.3 → 2.0.0)
./scripts/release.sh --increment major

# Specific version
./scripts/release.sh --version 1.5.0

# Test what would happen (dry run)
./scripts/release.sh --increment patch --dry-run
```

### What Happens During a Release

1. **Validation**: Checks git repository state and current version
2. **Cleanup**: Removes build artifacts (`build/`, `dist/`, `*.egg-info/`)
3. **Version Update**: Updates version in `pyproject.toml` and other files
4. **Git Operations**: Commits changes, creates tag, and pushes to GitHub
5. **Package Build**: Creates wheel and source distributions in `dist/`
6. **PyPI Publish**: Uploads to PyPI (if `--publish` flag used)
7. **GitHub Release**: Creates release with changelog (if GitHub CLI available)
8. **🤖 MCP Server Sync**: Automatically triggers MCP server update workflow

When you create a release, the GitHub Actions workflow will automatically:
- Install the new client version
- Scan for `@mcp_tool()` decorated methods
- Generate updated MCP server tools
- Create a pull request in the MCP server repository

See `scripts/README.md` for detailed documentation and troubleshooting.

<div align="center">
<br></br>
<br></br>
Thanks for trying xplainable!
<br></br>
<strong>Made with ❤️ in Australia</strong>
<br></br>
<hr>
&copy; copyright xplainable pty ltd
</div>


