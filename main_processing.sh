# # Runs the complete analysis on a set of raw data of D0 meson decays to obtain the asymmetry in local regions of the phase space. The output is stored in the specified directory, and is organized in several directories generated by this same script. Take into account that if a directory with the same name already exists this code might not work as intended. Note that making changes to any of the individual scripts while this code is running can lead to a malfunction.
# # When running the code the output directory, the year the data to be analysed was taken, the size of the data to be analysed and whether or not the data should be binned when fitting must be given as arguments, in that order. The year must be one of: 16, 17 or 18. The size must be one of: small, medium, large, 1, 2, 3, 4, 5, 6, 7 or 8. The binned fitting argument must either be y/Y or n/N.
# # Author: Marc Oriol Pérez (marc.oriolperez@student.manchester.ac.uk)
# # Last modified: 16th September 2023

directory=$1 # Directory in eos
size=$2
minsize=$3 # Does a loop for size in the range size to minsize
binned=$4



if [[ "$binned" != "y" ]]; then
    if [[ "$binned" != "Y" ]]; then
        if [[ "$binned" != "n" ]]; then
            if [[ "$binned" != "N" ]]; then
                echo "WARNING: You did not select a valid option for the binned fit"
                echo
                echo "An binned fit will be performed"
                binned="y"
            fi   
        fi
    fi
fi


# Create necessary directories to store output



mkdir "/eos/lhcb/user/l/lseelan/"$directory
mkdir "/eos/lhcb/user/l/lseelan/"$directory"/selected_data"

echo "The necessary directories have been created"
echo


# Run the code

if ! [[ "$minsize" =~ ^[0-9]+$ ]]; then
  echo "WARNING: You did not select a valid option for the minsize fit"
  echo
  echo "The selection will run over sizes in the array [10, ..., $size]"
  minsize=10
else
  echo "The selection will run over sizes in the array [$minsize,...,$size]"
fi
# Saves all years in one folder
while [ $size -ge $minsize ]; do
    echo "Inside the loop. Size: $size"
    for year in 16 17 18; do 
        echo "Year" $year
        python selection_of_events.py --year $year --size $size --path "/eos/lhcb/user/l/lseelan/"$directory"/selected_data"

        echo
        for polar in up down
        do

            python multiple_candidates.py --year $year --size $size --polarity $polar --path "/eos/lhcb/user/l/lseelan/"$directory"/selected_data"
        done
        echo "Multiple candidates have been removed"
    done
    size=$((size - 10))  # For example, decrease 'size' by 10 in each iteration
done

## Double check "*_clean.root" not anything else
#################################################################################
#################################################################################
#################################################################################

# Remove files that don't end with "_clean.root"
find "/eos/lhcb/user/l/lseelan/"$directory"/selected_data" -type f ! -name '*_clean.root' -exec rm -f {} +

# list the remaining files (those ending with "_clean.root")
find "/eos/lhcb/user/l/lseelan/"$directory"/selected_data"  -type f -name '*_clean.root'

# echo "Unneccesary files have been removed"
