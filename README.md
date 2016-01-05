[![Build Status](https://travis-ci.org/thearn/solar_energy_calculator.svg?branch=master)](https://travis-ci.org/thearn/solar_energy_calculator)
Solar energy budget calculator
===============================

<center>
	<img src="images/header1.jpg" width="30%">
	<br>
	<img src="images/header.png" width="75%">
	<br>
	<img src="images/header3.png" width="75%">
</center>

[Jump over to example notebook](examples.ipynb) 

--------

This is a python code that implements a simple power budget model for the sizing and
analysis of ground-based photo-voltaic energy systems, included battery storage. I've written it primary with small-power hobby or residential applications in mind.

The core of this code is a model which implements a transient power balance
calculation, culminating in a time integration of a battery bank state-of-charge over time. This allows a user to very easily size a solar panel array and battery bank together for their intended application. It's a reasonably low fidelity model, and only takes a few seconds to run.

This model was written using NASA's OpenMDAO framework, and makes use of data from
the U.S. Department of Energy's National Renewable Energy Laboratory (NREL).

The core components of the model are contained in `solar.py`. The file `basic.py` includes an example
model of powered loads and overall problem specification. This is used to 
make the example IPython notebook, `solar.ipynb`. A more complex example is shown in `greenhouse.py`.

This is very much a work-in-progress. I am not an electrical engineer by training, but I do multidisciplinary systems analysis and optimization. It's my goal for the model to be sufficient for the design of real-world low power systems (see below for a list of projects that I have in mind).

Requirements
---------------
- Python 2.7/3.4 or higher
- Numpy, scipy, and matplotlib. It's probably best to use a system package manager or a distribution like [Anaconda](https://www.continuum.io/downloads) to set these up
- [OpenMDAO 1.0](http://openmdao.org/) or greater: `pip install openmdao` or clone and install from Github
- [Requests](http://docs.python-requests.org/en/latest/) module, to collect data from NREL's servers `pip install requests`
- [IPython/Jupyter](http://ipython.org/), to run the examples notebook `pip install jupyter`
- A small test file can be run to verify that everything is set up: `cd lib; python test_run.py` 

Summary of IPython notebook example
---------------------
The examples notebook provides an interactive interface to the simple model in `basic.py`. It produces a visualization of the performance of a photovoltaic 
energy collection and storage system over the course of one year of operation on an hour-by-hour basis, based on a variety of parameters:

 - Geographic location
 - PV array size (in rated watts) and orientation
 - Battery bank size (in watt-hours)
 - Power usage (load) specification (constant, daytime, night time, or direct PV load)

Using location-based data, the time series model then simulates one-year of 
operation of the described system, on an hour-by-hour basis. 

Below is an example
of the figure produced for a 100w panel + 360 Watt-hour battery system powering a constant 5 Watt load (lights or sensors, etc.):

<div style="text-align:center">
	<img src="images/result_ex2.png" width="75%">
</div>

This transient analysis is what differentiates this code from other solar energy calculators. Full examples with design considerations, descriptions of the plot information, and output interpretation are given in the [examples notebook](examples.ipynb).


More in-depth customization
==========================
You can create a much more customized model than what is provided in the notebook by directly implementing your own OpenMDAO model that uses the components in `solar.py`. For example, see `greenhouse.py`, which implements a load component with temperature logic, time-of-day logic, etc. The data source component that parses the NREL data also provides solar cell temperature, wind speed values, solar irradiance, and hour of day information that can be used to describe transient power loads.

Some background on my motivations: I have a few acres of land with decent line-of-sight to the sun, and (despite the sometimes difficult Great Lakes climate) I have ideas for a couple of different solar electric projects that can be informed by this model:

- A small automated off-grid greenhouse that will pump water for irrigation, ventilate the space when it is too warm, regularly upload imaging data over Wifi (for, say, computer vision processing to analyze plant growth and harvest potential) and provide on-demand and maintenance charging for my Li-Ion handheld tool batteries. This is the model that is implemented in `greenhouse.py`.
- A solar thermal kiln for drying firewood, with circulation fan and small night spotlight. In this case, I would be most likely to power the fan from a PV source directly and would not need to size a battery for it. For the light, there are decent of the shelf panel+light+battery systems that are already sized and reasonably priced. There isn't much practical advantage to coupling the two power systems together. But the model can still give me an idea of effective up-time for these loads.
- My property has a drilled well that isn't currently used (capped tight but not filled in). The ground water in my area is not very good, it has a lot of dissolved minerals and other impurities. I'd like to sample it to determine what is really in the water, and look into reactivating it (with guidance from the local authorities) for irrigation use. This would be with an automated solar-powered system to pump it up (only 50' or so), purify it if necessary (via distillation or reverse osmosis) and pump it into rain barrels for use by other automated systems.

When I get around to testing a model of one of these and physically building any of them, I will include documentation of it within this repo in separate READMEs.

Future plans
==================
There are a lot of possible improvements and enhancements:
 
 - NREL has an [API](https://developer.nrel.gov/docs/solar/pvwatts-v5/) which could be used to automatically get the data
 
 - Modeling of system voltage matching and PWM vs. MPPT controller technologies
 
 - More sophisticated battery component with voltage estimation and temperature dependent discharge curves and charge characteristics
 
 - Create a version of the model that allows for battery SOC-dependent load calculations. For example, maybe I would like to implement a load that only powers when the battery SOC is above a certain percentage. The power draw of some loads may also change based on battery voltage, which is tied to battery SOC (such as an unregulated voltage supplied to an LED). This would introduce an implicit cycle: Loads -> BatterySOC -> Loads [...] that would have to be converged with a numerical solver. OpenMDAO is designed to recognize and converge implicit models like this automatically, though they are more computationally expensive than direct feed-forward only models. 
 
 - Include estimation of PV, battery, and load currents, which (together with voltage drop estimation) could be used to size wiring and appropriate fusing, with feed back into SOC calculation (charge/discharge rates).
 
 - As the battery charge calculation becomes more sophisticated (particularly if it becomes part of a larger implicit system), it would likely be more advantageous to implement an improved numerical integration scheme, such as [implicit collocation methods](https://en.wikipedia.org/wiki/Collocation_method). This would allow for effective simultaneous analysis and optimization. 
 
 - Implementation of numerical derivatives using OpenMDAO's derivative API. This will allow for fast and efficient numerical optimization, even on extremely large design spaces, particularly when coupled with other codes. For instance, one could use it to optimize a power load schedule over time with respect to battery, thermal, cost, or operational constraints, etc. I've already implemented derivatives within a few of the components.
 
 - Components for hybrid solar+wind energy collection and distribution. NREL has a set of Python-based wind energy models within their [WISDEM](http://www.nrel.gov/wind/systems_engineering/models_tools.html?print) tool (which is also written using OpenMDAO), though these are much more in-depth than the model provided here.
