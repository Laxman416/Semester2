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
                The argument must be one of: [large, small, medium, 1-8]. The integers specify the number of root
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
        choices=[16,17,18,19],
        required=True,
        help="flag to set the data taking year."
    )
    parser.add_argument(
        "--size",
        type=str,
        choices=["large", "medium", "small", "1", "2", "3", "4", "5", "6", "7", "8"],
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
args = parse_arguments()
# Bin Parameters
numbins = 240
lower_boundary = 1815
upper_boundary = 1910

if args.binned_fit=="y" or args.binned_fit=="Y":
    binned = True
else:
    binned = False

ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.ERROR) # mute RooFit warnings

if args.year == 19:
    if args.scheme == "total":
        # Selects invariant mass (D0_MM) of DO
        ttree_D0 = TChain("D02Kpi_Tuple/DecayTree")
        ttree_D0.Add(f"{args.input}/D0_up_data_16_{args.size}_clean.root")
        ttree_D0.Add(f"{args.input}/D0_up_data_17_{args.size}_clean.root")
        ttree_D0.Add(f"{args.input}/D0_up_data_18_{args.size}_clean.root")
        ttree_D0.Add(f"{args.input}/D0_down_data_16_{args.size}_clean.root")
        ttree_D0.Add(f"{args.input}/D0_down_data_17_{args.size}_clean.root")
        ttree_D0.Add(f"{args.input}/D0_down_data_18_{args.size}_clean.root")
        ttree_D0.SetBranchStatus("*", 0)
        ttree_D0.SetBranchStatus("D0_MM", 1)


        # Selects invariant mass (D0_MM) of DObar
        ttree_D0bar = TChain("D02Kpi_Tuple/DecayTree")
        ttree_D0bar.Add(f"{args.input}/D0bar_up_data_16_{args.size}_clean.root")
        ttree_D0bar.Add(f"{args.input}/D0bar_up_data_17_{args.size}_clean.root")
        ttree_D0bar.Add(f"{args.input}/D0bar_up_data_18_{args.size}_clean.root")
        ttree_D0bar.Add(f"{args.input}/D0bar_down_data_16_{args.size}_clean.root")
        ttree_D0bar.Add(f"{args.input}/D0bar_down_data_17_{args.size}_clean.root")
        ttree_D0bar.Add(f"{args.input}/D0bar_down_data_18_{args.size}_clean.root")
        ttree_D0bar.SetBranchStatus("*", 0)
        ttree_D0bar.SetBranchStatus("D0_MM", 1)
    else:
        # Selects invariant mass (D0_MM) of DO for MagUp
        #Total years Bins
        ttree_D0 = TChain("D02Kpi_Tuple/DecayTree")
        ttree_D0.Add(f"{args.input}/D0_{args.year}_{args.size}_bin{args.bin}.root")
        ttree_D0.SetBranchStatus("*", 0)
        ttree_D0.SetBranchStatus("D0_MM", 1)

        # Selects invariant mass (D0_MM) of DObar for MagDown
        ttree_D0bar_up = TChain("D02Kpi_Tuple/DecayTree")
        ttree_D0bar_up.Add(f"{args.input}/D0bar_{args.year}_{args.size}_bin{args.bin}.root")
        ttree_D0bar_up.SetBranchStatus("*", 0)
        ttree_D0bar_up.SetBranchStatus("D0_MM", 1)

D0_M = ROOT.RooRealVar("D0_MM", "D0 mass / [MeV/c*c]", 1815, 1910)

# Johnson SU Distribution
Jmu = RooRealVar("Jmu", "Jmu", 1865, 1860, 1870)
Jlam = RooRealVar("Jlam", "Jlam", 16.3, 10, 20)
Jgam = RooRealVar("Jgam", "Jgam", 0.3, 0, 10)
Jdel = RooRealVar("Jdel", "Jdel", 1.6, 0, 10)
Johnson = RooJohnson("Johnson","Johnson", D0_M, Jmu, Jlam, Jgam, Jdel)

# Bifurcated Gaussian
bifurmean = RooRealVar("bifurmean", "bifurmean", 1865.2, 1860, 1870)
sigmaL =  RooRealVar("sigmaL", "sigmaL", 8.24, 0, 10)
sigmaR = RooRealVar("sigmaR", "sigmaR", 6.1, 0, 10)
bifurgauss = RooBifurGauss("Bifurgauss", "Bifurgauss", D0_M, bifurmean, sigmaL, sigmaR)

# Bifurcated Gaussian 
bifurmean2 = RooRealVar("bifurmean2", "bifurmean2", 1865.5, 1860, 1870)
sigmaL2 =  RooRealVar("sigmaL2", "sigmaL2", 6, 0, 10)
sigmaR2 = RooRealVar("sigmaR2", "sigmaR2", 8.49, 0, 10)
bifurgauss2 = RooBifurGauss("Bifurgaussian2", "Bifurgaussian2", D0_M, bifurmean2, sigmaL2, sigmaR2)

# Model Exponential Background
a0 = RooRealVar("a0", "a0", -0.009, -1, 0)
background = RooExponential("exponential", "exponential", D0_M, a0)

# Ratio of signal intensities between each model. For N PDFs need N-1 fractions 
# DO 
frac_D0 = RooRealVar("frac_D0", "frac_D0", 0.16, 0, 1)
frac_D0_2 = RooRealVar("frac_D0_2", "frac_D0_2", 0.4, 0, 1)

# D0bar 
frac_D0bar = RooRealVar("frac_D0bar", "frac_D0bar", 0.3, 0, 1)
frac_D0bar_2 = RooRealVar("frac_D0bar_2", "frac_D0bar_2", 0.6, 0, 1)

# Generate normalisation variables
Nsig_D0 = ROOT.RooRealVar("Nsig_D0", "Nsig_D0", 0.95*ttree_D0.GetEntries(), 0, ttree_D0.GetEntries())
Nsig_D0bar = ROOT.RooRealVar("Nsig_D0bar", "Nsig_D0bar", 0.95*ttree_D0bar.GetEntries(), 0, ttree_D0bar.GetEntries())
Nbkg_D0 = ROOT.RooRealVar("Nbkg_D0", "Nbkg_D0", 0.05*ttree_D0.GetEntries(), 0, ttree_D0.GetEntries())
Nbkg_D0bar = ROOT.RooRealVar("Nbkg_D0bar", "Nbkg_D0bar", 0.05*ttree_D0bar.GetEntries(), 0, ttree_D0bar.GetEntries())

if binned:
    # D0_Hist recalled from memory and saved to the local variable
    ttree_D0.Draw(f"D0_MM>>D0_Hist({numbins},{lower_boundary},{upper_boundary})")
    D0_Hist = ROOT.gPad.GetPrimitive("D0_Hist")

    ttree_D0bar.Draw(f"D0_MM>>D0bar_Hist({numbins},{lower_boundary},{upper_boundary})")
    D0bar_Hist = ROOT.gPad.GetPrimitive("D0bar_Hist")


    Binned_D0 = RooDataHist("Binned_D0", ROOT.RooStringView("Binned D0 Data"), RooArgList(D0_M), D0_Hist)
    Binned_D0bar = RooDataHist("Binned_D0bar", ROOT.RooStringView("Binned D0bar Data"), RooArgList(D0_M), D0bar_Hist)

    # Creating the binned sample and simultaneous PDF
    binned_sample = ROOT.RooCategory("binned_sample", "binned_sample")
    simultaneous_pdf = ROOT.RooSimultaneous("simultaneous", "simultaneous", binned_sample)

    # Model Signal for D0 
    binned_sample.defineType("Binned_D0_sample")
    signal_D0 = RooAddPdf("signal_D0", "signal D0", RooArgList(Johnson, bifurgauss, bifurgauss2), RooArgList(frac_D0, frac_D0_2))
    # Generate model for D0
    model_D0 = RooAddPdf("model_D0", "model D0", [signal_D0, background], [Nsig_D0, Nbkg_D0])
    simultaneous_pdf.addPdf(model_D0, "Binned_D0_sample")
    
    # Model Signal for D0 MagDown
    binned_sample.defineType("Binned_D0bar_sample")
    signal_D0bar = RooAddPdf("signal_D0bar", "signal D0bar", RooArgList(Johnson, bifurgauss, bifurgauss2), RooArgList(frac_D0bar, frac_D0bar_2))
    # Generate model for D0bar
    model_D0bar = RooAddPdf("model_D0bar", "model D0bar", [signal_D0bar, background], [Nsig_D0bar, Nbkg_D0bar])
    simultaneous_pdf.addPdf(model_D0bar, "Binned_D0bar_sample")

    # Recombine the data into a simultaneous dataset
    imports = [ROOT.RooFit.Import("Binned_D0_sample", Binned_D0), ROOT.RooFit.Import("Binned_D0bar", Binned_D0bar)]
    simultaneous_data = RooDataHist("simultaneous_data", "simultaneous data", RooArgList(D0_M), ROOT.RooFit.Index(binned_sample), *imports)

    # Performs the simultaneous fit
    #enableBinIntegrator(model_D0_down, numbins)
    fitResult = simultaneous_pdf.fitTo(simultaneous_data, IntegrateBins = 1e-3, PrintLevel=-1, Save=True, Extended=True)

fitResult.Print()

# Get results
if args.year == 19:
    if args.scheme == 'total': 
        parameters = np.array([a0.getValV(), frac_D0.getValV(), frac_D0_2.getValV(), frac_D0bar.getValV(), frac_D0bar_2.getValV(), Nsig_D0.getValV(), Nbkg_D0.getValV(), Nsig_D0bar.getValV(), Nbkg_D0bar.getValV(), sigmaL.getValV(), sigmaR.getValV(), sigmaL2.getValV(), sigmaR2.getValV(), Jmu.getValV(), Jlam.getValV(), Jgam.getValV(), Jdel.getValV(), bifurmean.getValV(), bifurmean2.getValV(), Nsig_D0.getError(), Nsig_D0bar.getError()])
    #else:
        #parameters = np.array([a0.getValV(), frac_D0.getValV(), frac_D0_2.getValV(), frac_D0bar.getValV(), frac_D0bar_2.getValV(), Nsig_D0.getValV(), Nbkg_D0.getValV(), Nsig_D0bar.getValV(), Nbkg_D0bar.getValV(), Nsig_D0bar_down.getValV(), Nbkg_D0bar_down.getValV(), Nsig_D0bar_up.getValV(), Nbkg_D0bar_up.getValV(), sigmaL.getValV(), sigmaR.getValV(), sigmaL2.getValV(), sigmaR2.getValV(), frac_D0_down_2.getValV(), frac_D0_up_2.getValV(), frac_D0bar_down_2.getValV(), frac_D0bar_up_2.getValV(), Jmu.getValV(), Jlam.getValV(), Jgam.getValV(), Jdel.getValV(), bifurmean.getValV(), bifurmean2.getValV(),  Nsig_D0_down.getError(), Nsig_D0_up.getError(), Nsig_D0bar_down.getError(), Nsig_D0bar_up.getError()])np.savetxt(f"{args.path}/fit_parameters.txt", parameters, delimiter=',')
np.savetxt(f"{args.path}/fit_parameters.txt", parameters, delimiter=',')
print("My program took", time.time() - start_time, "to run")