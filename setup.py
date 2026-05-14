import os
from setuptools import setup
from setuptools.command.install import install

# Tente d'importer le logo depuis le package
# Note: Cela peut échouer si le package n'est pas encore complètement installé
try:
    from cygnisai_sdk_python._logo import CYGNIS_LOGO
except ImportError:
    CYGNIS_LOGO = "CygnisAI SDK" # Fallback si le logo n'est pas trouvé

class CustomInstallCommand(install):
    """
    Commande d'installation personnalisée pour tenter d'afficher un message
    et le logo après l'installation standard.
    """
    def run(self):
        install.run(self) # Exécute la commande d'installation standard
        # Tente d'afficher le logo. La visibilité de cette sortie dépend de pip et de l'environnement.
        print("\n" + "="*80)
        print("Merci d'avoir installé le SDK CygnisAI !")
        print(CYGNIS_LOGO)
        print("Vous pouvez maintenant utiliser 'import cygnisai_sdk_python' dans vos projets.")
        print("="*80 + "\n")

setup(
    cmdclass={
        'install': CustomInstallCommand,
    },
    # Les autres métadonnées du package sont gérées par pyproject.toml
    # setuptools lira pyproject.toml pour les informations de base du package
)
