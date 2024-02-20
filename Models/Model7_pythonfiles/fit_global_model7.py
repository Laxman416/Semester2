"""
fit_global.py

Gauss Bifurcated Johnson

This code is used to perform a global fit on the selected data. In order to do so a simulatenous fit is done on the four datasets (with different mesons and polarities). This simulatenous fit keeps all variables constant across the four fits except for the normalisation constants which are allowed to vary independently. The model used consists of a Crystal Ball function and a Gaussian distribution to model the signal and an Exponential decay to model the background.
The year of interest and size of the data to be analysed must be specified using the required flags --year --size. It is necessary to specify if the fit should be performed on the binned data or the unbinned data using the flag --binned_fit. There is a flag --path, which is not required. This one is used to specify the directory where the input data is located, and where the output file should be written. By default it is set to be the current working directory.
It outputs the value of the constants shared in the simultaneous fit to a text file. This code is heavily inspired by Marc Oriol Pérez (marc.oriolperez@student.manchester.ac.uk), however it has been redesigned so that the binned fit is succesfully performed.

Author: Sam Taylor (samuel.taylor-9@student.manchester.ac.uk) and Laxman Seelan (laxman.seelan@student.manchester.ac.uk)
Last edited: 5th November 2023
"""

import ROOT
import numpy as np
import uproot
import argparse
import os
from ROOT import TChain, RooRealVar, RooDataSet, RooGaussian, RooCrystalBall, RooAddPdf, RooArgList, RooFit, RooArgSet, RooDataHist, RooExponential, RooLinkedList, RooBifurGauss, RooJohnson, RooGExpModel
import time 
start_time = time.time()
def dir_path(string):
    '''
    Checks if a given string is the path to a directory.
    If affirmative, returns the string. If negative, gives an error.
    '''
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)
        
def parse_arguments():
    '''
    Parses the arguments needed along the code. Arguments:
    
    --year      Used to specify the year at which the data was taken the user is interested in.
                The argument must be one of: [16, 17, 18]. These referr to 2016, 2017 & 2018, respectively.
    --size      Used to specify the amount of events the user is interested in analysing.
                The argument must be one of:  [1-800]. The integers must be in steps of 10. The integers specify the number of root
                files to be read in.
                files to be read in. Large is equivalent to 8. Medium is equivalent to 4. Small takes 200000 events.
    --polarity  Used to specify the polarity of the magnet the user is interested in.
                The argument must be one of: [up, down].
                in the case it is not specified, the default path is the current working directory.
    --binned_fit
                Used to specify if the data should be binned before performing the fit or an unbinned fit should be performed.
                Type either y or Y for a binned fit. Type n or N for an unbinned fit.
    
    Returns the parsed arguments.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--year",
        type=int,
        choices=[16,17,18],
        required=True,
        help="flag to set the data taking year."
    )
    parser.add_argument(
        "--size",
        type=size_argument,
        required=True,
        help="flag to set the data taking year."
    )   
    parser.add_argument(
        "--path",
        type=dir_path,
        required=False,
        default=os.getcwd(),
        help="flag to set the path where the output files should be written to"
    )
    parser.add_argument(
        "--binned_fit",
        type=str,
        choices=["y", "Y", "n", "N"],
        required=True,
        help="flag to set whether a binned or an unbinned should be performed (y/n)"
    )
    parser.add_argument(
        "--input",
        type=dir_path,
        required=False,
        default=os.getcwd(),
        help="flag to set the path where the input files should be read"
    )
    parser.add_argument(
        "--scheme",
        type=str,
        choices=["total","pT_eta","pT","eta"],
        required=True,
        help="flag to set which binning scheme to use"
    )
    parser.add_argument(
        "--bin",
        type=str,
        required=False,
        help="flag to set whether a binned or an unbinned should be performed (y/n)"
    )
    
    return parser.parse_args()
def enableBinIntegrator(func, num_bins):
    """
    Force numeric integration and do this numeric integration with the
    RooBinIntegrator, which sums the function values at the bin centers.
    """
    custom_config = ROOT.RooNumIntConfig(func.getIntegratorConfig())
    custom_config.method1D().setLabel("RooBinIntegrator")
    custom_config.getConfigSection("RooBinIntegrator").setRealValue("numBins", num_bins)
    func.setIntegratorConfig(custom_config)
    func.forceNumInt(True)

def disableBinIntegrator(func):
    """
    Reset the integrator config to disable the RooBinIntegrator.
    """
    func.setIntegratorConfig()
    func.forceNumInt(False)

def size_argument(value):
    if value.isdigit():
        # If the input is a digit, treat it as an integer
        int_value = int(value)
        if 1 <= int_value <= 800 and int_value % 10 == 0: 
            return int_value
        else:
            raise argparse.ArgumentTypeError("Integer value must be between 1 and 800 and be divisible by 10.")
    else:
        raise argparse.ArgumentTypeError("Invalid value.Choose an integer between 1 and 800 that is divisible by 10.")

def generate_list(size_value_local):
    result_list = []
    current_value = 10

    while not result_list or result_list[-1] < size_value_local:
        result_list.append(current_value)
        current_value += 10

    return result_list

# - - - - - - - MAIN BODY - - - - - - - #
args = parse_arguments()
# Bin Parameters
numbins = 300
lower_boundary = 1815
upper_boundary = 1910

if args.binned_fit=="y" or args.binned_fit=="Y":
    binned = True
else:
    binned = False
ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR) # mute RooFit warnings
ttree_D0_up = TChain("D02Kpi_Tuple/DecayTree")
ttree_D0_down = TChain("D02Kpi_Tuple/DecayTree")
ttree_D0bar_up = TChain("D02Kpi_Tuple/DecayTree")
ttree_D0bar_down = TChain("D02Kpi_Tuple/DecayTree")

size_value = args.size
if isinstance(size_value, int):
    size_value = int(size_value)
    size_list = generate_list(size_value)
    for valuesize in size_list:
      if args.scheme == "total":

          # Selects invariant mass (D0_MM) of DO for MagUp
          ttree_D0_up.Add(f"{args.input}/20{args.year}/up/D0/D0_up_data_{args.year}_{args.size}_clean.root")
          ttree_D0_up.SetBranchStatus("*", 0)
          ttree_D0_up.SetBranchStatus("D0_MM", 1)

          # Selects invariant mass (D0_MM) of DO for MagDown
          ttree_D0_down.Add(f"{args.input}/20{args.year}/down/D0/D0_down_data_{args.year}_{args.size}_clean.root")
          ttree_D0_down.SetBranchStatus("*", 0)
          ttree_D0_down.SetBranchStatus("D0_MM", 1)

          # Selects invariant mass (D0_MM) of DObar for MagDown
          ttree_D0bar_up.Add(f"{args.input}/20{args.year}/up/D0bar/D0bar_up_data_{args.year}_{args.size}_clean.root")
          ttree_D0bar_up.SetBranchStatus("*", 0)
          ttree_D0bar_up.SetBranchStatus("D0_MM", 1)

          # Selects invariant mass (D0_MM) of DObar for MagDown
          ttree_D0bar_down.Add(f"{args.input}/20{args.year}/down/D0bar/D0bar_down_data_{args.year}_{args.size}_clean.root")
          ttree_D0bar_down.SetBranchStatus("*", 0)
          ttree_D0bar_down.SetBranchStatus("D0_MM", 1)
      else:
          # Selects invariant mass (D0_MM) of DO for MagUp
          ttree_D0_up = TChain("D02Kpi_Tuple/DecayTree")
          ttree_D0_up.Add(f"{args.input}/D0_up_{args.year}_{args.size}_bin{args.bin}.root")
          ttree_D0_up.SetBranchStatus("*", 0)
          ttree_D0_up.SetBranchStatus("D0_MM", 1)

          # Selects invariant mass (D0_MM) of DO for MagDown
          ttree_D0_down = TChain("D02Kpi_Tuple/DecayTree")
          ttree_D0_down.Add(f"{args.input}/D0_down_{args.year}_{args.size}_bin{args.bin}.root")
          ttree_D0_down.SetBranchStatus("*", 0)
          ttree_D0_down.SetBranchStatus("D0_MM", 1)

          # Selects invariant mass (D0_MM) of DObar for MagDown
          ttree_D0bar_up = TChain("D02Kpi_Tuple/DecayTree")
          ttree_D0bar_up.Add(f"{args.input}/D0bar_up_{args.year}_{args.size}_bin{args.bin}.root")
          ttree_D0bar_up.SetBranchStatus("*", 0)
          ttree_D0bar_up.SetBranchStatus("D0_MM", 1)

          # Selects invariant mass (D0_MM) of DObar for MagDown
          ttree_D0bar_down = TChain("D02Kpi_Tuple/DecayTree")
          ttree_D0bar_down.Add(f"{args.input}/D0bar_down_{args.year}_{args.size}_bin{args.bin}.root")
          ttree_D0bar_down.SetBranchStatus("*", 0)
          ttree_D0bar_down.SetBranchStatus("D0_MM", 1)


D0_M = ROOT.RooRealVar("D0_MM", "D0 mass / [MeV/c*c]", 1815, 1910)

# Johnson SU Distribution
Jmu = RooRealVar("Jmu", "Jmu", 1865, 1863, 1867)
Jlam = RooRealVar("Jlam", "Jlam", 18.7, 10, 20)
Jgam = RooRealVar("Jgam", "Jgam", 0.45, 0, 10)
Jdel = RooRealVar("Jdel", "Jdel", 2.12, 0, 10)
Johnson = RooJohnson("Johnson","Johnson", D0_M, Jmu, Jlam, Jgam, Jdel)

# Bifurcated Gaussian
mean = RooRealVar("mean", "mean", 1865, 1850, 1880)
sigmaL =  RooRealVar("sigmaL", "sigmaL", 5.23, 0, 10)
sigmaR = RooRealVar("sigmaR", "sigmaR", 6.8, 0, 10)
bifurgauss = RooBifurGauss("Bifurgauss", "Bifurgauss", D0_M, mean, sigmaL, sigmaR)

# Model Gaussians

mean = RooRealVar("mean", "mean", 1865, 1850, 1880)
sigma = RooRealVar("sigma", "sigma", 6.57, 0, 20)
gaussian = RooGaussian("gauss", "gauss", D0_M, mean, sigma)

# Model Exponential Background
a0 = RooRealVar("a0", "a0", -0.009, -1, 0)
background = RooExponential("exponential", "exponential", D0_M, a0)

# Ratio of signal intensities between each model. For N PDFs need N-1 fractions 
# D0 MagDown
frac_D0_down = RooRealVar("frac_D0_down", "frac_D0_down", 0.18, 0.1, 1) 
frac_D0_down_2 = RooRealVar("frac_D0_down_2", "frac_D0_down_2", 0.40, 0, 1) 
# DO MagUp
frac_D0_up = RooRealVar("frac_D0_up", "frac_D0_up", 0.21, 0.1, 1) 
frac_D0_up_2 = RooRealVar("frac_D0_up_2", "frac_D0_up_2", 0.36, 0, 1) 
# D0bar MagDown
frac_D0bar_down = RooRealVar("frac_D0bar_down", "frac_D0bar_down", 0.18, 0.1, 1) 
frac_D0bar_down_2 = RooRealVar("frac_D0bar_down_2", "frac_D0bar_down_2", 0.40, 0, 1) 
# D0bar MagUp2
frac_D0bar_up = RooRealVar("frac_D0bar_up", "frac_D0bar_up", 0.23, 0.1, 1) 
frac_D0bar_up_2 = RooRealVar("frac_D0bar_up_2", "frac_D0bar_up_2", 0.37, 0, 1) 

# Generate normalisation variables
Nsig_D0_up = ROOT.RooRealVar("Nsig_D0_up", "Nsig_D0_up", 0.95*ttree_D0_up.GetEntries(), 0, ttree_D0_up.GetEntries())
Nsig_D0bar_up = ROOT.RooRealVar("Nsig_D0bar_up", "Nsig_D0bar_up", 0.95*ttree_D0bar_up.GetEntries(), 0, ttree_D0bar_up.GetEntries())
Nbkg_D0_up = ROOT.RooRealVar("Nbkg_D0_up", "Nbkg_D0_up", 0.05*ttree_D0_up.GetEntries(), 0, ttree_D0_up.GetEntries())
Nbkg_D0bar_up = ROOT.RooRealVar("Nbkg_D0bar_up", "Nbkg_D0bar_up", 0.05*ttree_D0bar_up.GetEntries(), 0, ttree_D0bar_up.GetEntries())
Nsig_D0_down = ROOT.RooRealVar("Nsig_D0_down", "Nsig_D0_down", 0.95*ttree_D0_down.GetEntries(), 0, ttree_D0_down.GetEntries())
Nsig_D0bar_down = ROOT.RooRealVar("Nsig_D0bar_down", "Nsig_D0bar_down", 0.95*ttree_D0bar_down.GetEntries(), 0, ttree_D0bar_down.GetEntries())
Nbkg_D0_down = ROOT.RooRealVar("Nbkg_D0_down", "Nbkg_D0_down", 0.05*ttree_D0_down.GetEntries(), 0, ttree_D0_down.GetEntries())
Nbkg_D0bar_down = ROOT.RooRealVar("Nbkg_D0bar_down", "Nbkg_D0bar_down", 0.05*ttree_D0bar_down.GetEntries(), 0, ttree_D0bar_down.GetEntries())


if binned:
    # Creating the histograms for both polarities for D0 and D0bar by converting the TTree D0_MM data inside the TChain to a TH1(base class of ROOT histograms)
    # TTree.Draw plots a histogram with name D0_Up_Hist and given bin parameters and saves it to memory using: >>
    ttree_D0_up.Draw(f"D0_MM>>D0_Up_Hist({numbins},{lower_boundary},{upper_boundary})")
    # D0_Up_Hist recalled from memory and saved to the local variable
    D0_Up_Hist = ROOT.gPad.GetPrimitive("D0_Up_Hist")

    ttree_D0_down.Draw(f"D0_MM>>D0_Down_Hist({numbins},{lower_boundary},{upper_boundary})")
    D0_Down_Hist = ROOT.gPad.GetPrimitive("D0_Down_Hist")

    ttree_D0bar_up.Draw(f"D0_MM>>D0bar_Up_Hist({numbins},{lower_boundary},{upper_boundary})")
    D0bar_Up_Hist = ROOT.gPad.GetPrimitive("D0bar_Up_Hist")

    ttree_D0bar_down.Draw(f"D0_MM>>D0bar_Down_Hist({numbins},{lower_boundary},{upper_boundary})")
    D0bar_Down_Hist = ROOT.gPad.GetPrimitive("D0bar_Down_Hist")


    # Creating Binned container sets using RooDataHist
    Binned_D0_up = RooDataHist("Binned_D0_up", "Binned D0 Up Data", RooArgList(D0_M), D0_Up_Hist)
    Binned_D0_down = RooDataHist("Binned_D0_down", "Binned D0 Down Data", RooArgList(D0_M), D0_Down_Hist)
    Binned_D0bar_up = RooDataHist("Binned_D0bar_up", "Binned D0bar Up Data", RooArgList(D0_M), D0bar_Up_Hist)
    Binned_D0bar_down = RooDataHist("Binned_D0bar_down", "Binned D0bar Down Data", RooArgList(D0_M), D0bar_Down_Hist)

    # Creating the binned sample and simultaneous PDF
    binned_sample = ROOT.RooCategory("binned_sample", "binned_sample")
    simultaneous_pdf = ROOT.RooSimultaneous("simultaneous", "simultaneous", binned_sample)

    # Model Signal for D0 MagUp
    binned_sample.defineType("Binned_D0_up_sample")
    signal_D0_up = RooAddPdf("signal_D0_up", "signal D0 up", RooArgList(bifurgauss, gaussian, Johnson), RooArgList(frac_D0_up, frac_D0_up_2))
    # Generate model for D0 MagUp
    model_D0_up = RooAddPdf("model_D0_up", "model D0 up", [signal_D0_up, background], [Nsig_D0_up, Nbkg_D0_up])
    simultaneous_pdf.addPdf(model_D0_up, "Binned_D0_up_sample")
    
    # Model Signal for D0 MagDown
    binned_sample.defineType("Binned_D0_down_sample")
    signal_D0_down = RooAddPdf("signal_D0_down", "signal D0 down", RooArgList(bifurgauss, gaussian, Johnson), RooArgList(frac_D0_down, frac_D0_down_2))
    # Generate model for D0 MagDown
    model_D0_down = RooAddPdf("model_D0_down", "model D0 down", [signal_D0_down, background], [Nsig_D0_down, Nbkg_D0_down])
    simultaneous_pdf.addPdf(model_D0_down, "Binned_D0_down_sample")

    # Model Signal for D0bar MagUp
    binned_sample.defineType("Binned_D0bar_up_sample")
    signal_D0bar_up = RooAddPdf("signal_D0bar_up", "signal D0bar up", RooArgList(bifurgauss, gaussian, Johnson), RooArgList(frac_D0bar_up, frac_D0bar_up_2))
    # Generate model for D0bar MagUp
    model_D0bar_up = RooAddPdf("model_D0bar_up", "model D0bar up", [signal_D0bar_up, background], [Nsig_D0bar_up, Nbkg_D0bar_up])
    simultaneous_pdf.addPdf(model_D0bar_up, "Binned_D0bar_up_sample")

    # Model Signal for D0bar MagDown
    binned_sample.defineType("Binned_D0bar_down_sample")
    signal_D0bar_down = RooAddPdf("signal_D0bar_down", "signal D0bar down", RooArgList(bifurgauss, gaussian, Johnson), RooArgList(frac_D0bar_down, frac_D0bar_down_2))
    # Generate model for D0bar MagDown
    model_D0bar_down = RooAddPdf("model_D0bar_down", "model D0bar down", [signal_D0bar_down, background], [Nsig_D0bar_down, Nbkg_D0bar_down])
    simultaneous_pdf.addPdf(model_D0bar_down, "Binned_D0bar_down_sample")

    # Recombine the data into a simultaneous dataset
    imports = [ROOT.RooFit.Import("Binned_D0_up_sample", Binned_D0_up), ROOT.RooFit.Import("Binned_D0bar_up_sample", Binned_D0bar_up), ROOT.RooFit.Import("Binned_D0_down_sample", Binned_D0_down), ROOT.RooFit.Import("Binned_D0bar_down_sample", Binned_D0bar_down)]
    simultaneous_data = RooDataHist("simultaneous_data", "simultaneous data", RooArgList(D0_M), ROOT.RooFit.Index(binned_sample), *imports)

    # Performs the simultaneous fit
    #enableBinIntegrator(simultaneous_data, numbins)
    fitResult = simultaneous_pdf.fitTo(simultaneous_data, IntegrateBins = 1e-3, PrintLevel=-1, Save=True, Extended=True)
    #disableBinIntegrator(simultaneous_data)

# Prints the simultaneous fit parameters
fitResult.Print()

# Get results
#parameters = np.array([a0.getValV(), frac_D0_down.getValV(), frac_D0_up.getValV(), frac_D0bar_down.getValV(), frac_D0bar_up.getValV(), Nsig_D0_down.getValV(), Nbkg_D0_down.getValV(), Nsig_D0_up.getValV(), Nbkg_D0_up.getValV(), Nsig_D0bar_down.getValV(), Nbkg_D0bar_down.getValV(), Nsig_D0bar_up.getValV(), Nbkg_D0bar_up.getValV(), sigmaL.getValV(), sigmaR.getValV(),  sigma.getValV(), frac_D0_down_2.getValV(), frac_D0_up_2.getValV(), frac_D0bar_down_2.getValV(), frac_D0bar_up_2.getValV(), Jmu.getValV(), Jlam.getValV(), Jgam.getValV(), Jdel.getValV(), bifurmean.getValV(), mean.getValV(),  Nsig_D0_down.getError(), Nsig_D0_up.getError(), Nsig_D0bar_down.getError(), Nsig_D0bar_up.getError()])

variables = [a0, frac_D0_down, frac_D0_down_2, frac_D0_up, frac_D0_up_2, frac_D0bar_down, frac_D0bar_down_2, frac_D0bar_up, frac_D0bar_up_2, Nsig_D0_down, Nbkg_D0_down, Nsig_D0_up, Nbkg_D0_up, Nsig_D0bar_down, Nbkg_D0bar_down, Nsig_D0bar_up, Nbkg_D0bar_up, sigmaL, sigmaR, Jmu, Jlam, Jgam, Jdel, mean, sigma]
values = [var.getValV() for var in variables]
errors = [var.getError() for var in variables]
names = [var.GetName() for var in variables]

# Create a dictionary with variable names and values
parameters_dict = {name: value for name, value in zip(names, values)}

# Save the dictionary to a text file
with open(f"{args.path}/fit_parameters.txt", 'w') as file:
    for key, value in parameters_dict.items():
        file.write(f"{key}: {value}\n")
    for name, error in zip(names, errors):
        if name.startswith("Nsig_"):
            file.write(f"{name}_error: {error}\n")
print("My program took", time.time() - start_time, "to run")