# Making configuration files

This example shows how to create preprocessing and feature extraction configuration files in one of two ways.

## Guided generation

If you run pipeline_manager without providing a preprocessing or feature extraction configuration file, the code will prompt you through the generation of a simple yaml file.

This method is not recommended for more complex configuration files that include many steps or gridded/looped inputs.

## Writing a configuration file

Basic Yaml syntax is used to create a key that matches one of the method arguments for the preprocessing or feature method you wish to call, and then the value becomes the method arguments value. 

Example configuration files can be found in [configuration examples](config_examples/)

## Examples
An example preprocessing script without any loops is shown below:
```
frequency_downsample:
    step_nums:
        - 1
    input_hz:
        - None
    output_hz:
        - 256

butterworth_filter:
    step_nums:
        - 2
        - 3
        - 4
        - 5
    filter_type:
        - 'bandstop'
        - 'bandstop'
        - highpass
        - lowpass
    freq_filter_array: 
        - "[59,61]"
        - "[119,121]"
        - 1
        - 100
    butterorder:
        - 4
        - 4
        - 4
        - 4
```
The configuration file tells the code to do the following steps (set by `step_num`):
1. Downsample all data to 256 Hz.
2. Bandstop from 59-61 Hz
3. Bandstop from 119-121 Hz
4. Highpass data below 1 Hz.
5. Lowpass data higher than 100 Hz

An example feature configuration file using loops is shown below:
```
spectral_energy_welch:
    step_nums:
        - 1
        - 2:
            - 99
            - 1
    low_freq:
        - -np.inf
        - 0:
            - 99
            - 1
    hi_freq:
        - np.inf
        - 1:
            - 100
            - 1
    win_size:
        - 1
        - 1:
            - 99
    win_stride:
        - 0.5
        - 0.5:
            - 99
```
where we are escaping the need to explicitly write 100 steps by using a loop. A breakdwon of the example is as follows:
1. Get the spectral power from the entire dataset.
2. Start a loop where we take 99 steps, iterating by one each step
    1. Each new step increments by 1 Hz from 0 to 100
    2. We calculate the spectral power in that 1 Hz window
  
Generally, loops are created by creating an indented list below an entry. If there are two entries, the logic follows that the key (in the case of step_nums, '2') is the lower bound, the 99 is the upper bound, and the 1 is the step size.

If there is only one value, then the logic is that the key (in the case of win_size `1`) is repeated by the number of times shown by the indented value (`99`)
