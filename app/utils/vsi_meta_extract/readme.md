# Metadata Analysis Utility

First, ensure that you have:
1. A folder on your computuer containing a downloaded analysis. (This you can obtain by running through the https://vesseg.online workflow, producing evaluations, and then downloading everything from the project tab.)
2. A folder on your computer containing the original .vsi files.

Second, ensure that you have (assuming macOS):
1. [Docker installed](https://www.docker.com/get-started)
2. `git` on your computer
    1. Open a terminal window (i.e., type `cmd + Space` on your Mac, in the search bar enter `terminal`, press `Enter`)
    2. Type `git --version` at the command prompt in the terminal. If `git` is not installed, it will now guide you through the set-up.

 Third, clone the vesseg repository:
 1. In the terminal windown, navigate to a folder of your choice, i.e. by entering `cd ~/Documents` or (in German) `cd ~/Dokumente`.
 2. Now execute in the terminal:
```
git clone https://github.com/jacobmatthewmurray/vesseg.git
```
3. Enter the directory by entering `cd vesseg` and make a directory for your output `mkdir data`.
4. Now run 
```
cd app/utils/vsi_meta_extract
```
5. And then
```
./cmi.sh
```
6. Now it will build the necessary programs, when prompted enter
    1. /path/to/your/analysis_folder (from the first step, it usually looks like `/Users/your_username/Downloads/analysis`)
    2. /path/to/your/vsi_folder
    3. /path/to/some/output_folder (i.e., `/Users/your_username/Dokumente/vesseg/data`)
    4. _Note: to get `your_username` you can type `ls /users`_ 

 This should be it! Let me know, if you have questions. 


