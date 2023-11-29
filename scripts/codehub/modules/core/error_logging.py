import warnings
from sklearn.exceptions import ConvergenceWarning

"""
def save_warning_to_log(message, category, filename, lineno, file=None, line=None):
    with open(warning_log_file, "a") as f:
        f.write(f"{category.__name__} in {filename} at line {lineno}: {message}\n")

def log_mne_warnings(func):

    MNE complains about processing not taking place in MNE, so we just silence its warnings and save them.

    Not working yet. Issues trying to log warnings.

    def wrapper(*args, **kwargs):
        def custom_filter(action, category, filename, lineno, file=None, line=None):
            print("Testing")
            save_warning_to_log(
                f"Captured warning: {action} - {category.__name__} in {filename} at line {lineno}",
                category, filename, lineno, file, line
            )
            return None

        # Use warnings.catch_warnings to capture warnings and apply the custom filter
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", custom_filter)
            result = func(*args, **kwargs)

        # Optionally, you can process the caught_warnings list if needed
        for warning in caught_warnings:
            print(f"Caught a warning: {warning.message}")

        return result

    return wrapper
"""
            
def silence_mne_warnings(func):
    def wrapper(*args, **kwargs):
        # Use the warnings.filterwarnings context manager to temporarily filter out warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            result = func(*args, **kwargs)
        return result
    return wrapper