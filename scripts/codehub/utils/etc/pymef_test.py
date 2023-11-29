from pymef.mef_session import MefSession

session_path = '/Users/bjprager/Documents/GitHub/SCALP_CONCAT-EEG/user_data/sample_data/mef/bids_mef_3p0/sub-001/ses-01/eeg/sub-001_ses-01_task-example_eeg.mefd'
password     = 'password2'          # leave blank if no password

# read session metadata
ms       = MefSession(session_path, password)
mef_info = ms.read_ts_channel_basic_info()

# Get the channel names
keys       = [ival['name'] for ival in mef_info]
sample_map = [None for ival in keys]

# read data of multiple channels from beginning to end
data = ms.read_ts_channels_sample(keys, [sample_map])