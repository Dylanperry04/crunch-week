# Azure App Service deployment

## Connected CrunchWeek app

Azure Deployment Center added `.github/workflows/main_crunchweek.yml` for the **CrunchWeek** app in resource group **Crunchweek**. This workflow runs on `main` pushes or manually and uses the existing federated Azure login secrets. It now:

- Builds React and packages its compiled assets with the Python backend and locked dependencies.
- Sets startup to `bash azure-startup.sh` and enables remote Python builds; removes incompatible `WEBSITE_RUN_FROM_PACKAGE` configuration.
- Uses Azure's platform-provided `WEBSITE_HOSTNAME` for host validation, preserving any custom `ALLOWED_HOSTS` values.
- Waits for both `/api/health` and the compiled React page before reporting success.

No local environment files or AI/Notion secrets are read or changed by these steps. The Azure login needs permission to update this app's configuration and deploy its code. If the workflow fails at configuration, an operator can run these equivalent commands in **Bash Cloud Shell**, then retry the workflow after granting the deployment identity the necessary App Service permissions:

```bash
az webapp config set -g Crunchweek -n CrunchWeek --startup-file 'bash azure-startup.sh' --output none
az webapp config appsettings set -g Crunchweek -n CrunchWeek --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true --output none
az webapp config appsettings delete -g Crunchweek -n CrunchWeek --setting-names WEBSITE_RUN_FROM_PACKAGE --output none
```

Azure's default Python welcome page means the platform is running its placeholder application. A successful upload alone does not verify the FastAPI entry point or that the React assets were built. The connected workflow now verifies both.

## Optional publish-profile alternative

Repository publishing and Azure deployment are separate. The `Deploy Crunch Week to Azure (manual)` workflow only runs when explicitly started from Actions on `main`. This final code review did not change Azure resources or inspect local environment files.

Before running it:

1. Use an existing **Linux Python 3.12 App Service**. The workflow defaults to `CrunchWeek1`; select the correct existing app when starting it.
2. Enable App Service authentication and restrict access to your intended demo users. The app has one operator's credentials and no built-in user isolation.
3. Configure the App Service startup command as `bash azure-startup.sh`. The script runs one Uvicorn worker on the platform port, defaulting to 8000. A publish-profile deployment cannot set this startup command through the deploy action.
4. Set `SCM_DO_BUILD_DURING_DEPLOYMENT=true` so Azure installs the packaged Python requirements. Keep run-from-package disabled for this remote-build flow. The package already contains the built React assets.
5. Configure the app's existing AI/Notion settings in Azure App Service application settings, and add its hostname to `ALLOWED_HOSTS` along with `localhost,127.0.0.1`. Local environment files are not uploaded. React and FastAPI share one origin.
6. Add the app's publish profile as the new repository's `AZURE_WEBAPP_PUBLISH_PROFILE` Actions secret. The legacy secret name in the supplied workflow is also accepted if you explicitly configure it in this repository. Secrets do not transfer automatically from another repository. A publish profile requires the corresponding App Service deployment-auth settings to allow it.
7. Start the manual workflow. It runs backend/frontend checks, builds React and packages only runtime files, then deploys. Verify `/api/health`, the root page, and a small extraction after deployment.

To inspect the deployment ZIP locally after building React, run `python scripts/package_deployment.py`. It includes source, sample data, the compiled frontend and locked dependencies. It never includes environment files, Git history, node_modules or test data.

References: [Microsoft's Python App Service configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python) and [Azure's deploy action and publish-profile limitations](https://github.com/Azure/webapps-deploy).
