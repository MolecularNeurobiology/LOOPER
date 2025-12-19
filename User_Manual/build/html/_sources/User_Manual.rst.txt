
Startup Check List
==================

-  Power on the rigs

-  Power on the water baths

-  Check to make sure gas tank valves are open (down position for yellow
   knob)

-  Make sure the vacuum is on (Flowmeter: silver ball at 10 and black
   ball at 20)

-  Make sure all air bubbles are removed from the water baths

-  Each rig has its own set of calibration mask and face mask

-  ECG box is on and switch is on AC

-  Validyne box is on

-  Arduino is on

-  Git_PCC is running

-  And Finish Startup process is completed without issues

Materials List
==============

-  Impregum base pate + Catalyst Paste

-  Facemask – each rig should have its own set (pup and calibration
   facemask)

-  Swabs

-  Conductive Paste

-  ECG Leads – will need to be made so refer to wiki on instructions

-  Super glue

Important Notes Before Starting
===============================

-  Heed the advice given in the *order of operations* section below as
   it will streamline your operations.

-  **Facemask tips**

   -  **DO NOT** remove the facemasks from the respective rig.

   -  **IT IS IMPORTANT** to avoid getting any paste on the pups mouth or
      nose as it will impact the breathing and the run.

-  **ECG tips**

   -  **IT IS IMPORTANT** that none of the conductive paste spots of the
      leads overlap with each other; this will result in a noisy signal.

   -  It is best to place the red and black leads on with just the
      conductive paste first and verify a good signal being recorded in
      the GUI. This allows you to make adjustments without needing to
      rip off superglue, re-strip the wires, and reapply the conductive
      paste and glue every time.

   -  If you experience noise on the ECG channels, but have a decent
      signal, try gently pulling on the wires from behind to apply
      tension. Sometimes this helps the signal and resolves noise
      nicely.

-  Pay attention to the rigs during the startup process. This will be
   your best opportunity to find out if you will experience errors
   during your run that will prevent you from being able to use that
   recording.

-  Be sure to record all of the following metadata surrounding your
   experiments. These data are essential to record as they cannot be
   retroactively collected. Other data may be included in a datasheet
   you use during collection, but these data are the most essential.

   -  CUID

   -  RUID

   -  Sex

   -  Weight

   -  DOB

   -  Age

   -  Rig

   -  Number of run on that rig that day

   -  Gas tank ID (GUID)

-  Make notes on components that are not working or if you notice
   something out of the ordinary during the run. See *reporting errors*
   section below.

Order of Operations QuickStart
==============================

1. Turn on water heater and water pump.

2. Generate RUIDs for each mouse you intend to run on the Derived
   Resources database and enter just the CUID for each of those mice.
   Make 5 entries at a time (or however many rigs are currently
   functional).

3. Turn on each rig:

   a. Ensure you have a PM folder for your project on that rig.

   b. Run git_PCC and adjust all window sizes and settings.

   c. Push through the protocol until you get to Signal Preview 2 and
      save the file in the format RUID_date.

4. Go downstairs and get your mice.

5. By the time you get back upstairs, 45 minutes will have passed so you
   can immediately begin mounting mice.

6. Prior to preparing each mouse for the run, put a small dab of both
   the Impregum base paste with a small line of the catalyst next to
   each dab on the prep tray prior to mounting any pups.

   a. This saves a lot of time because for each rig as you go along you
      can immediately start mixing and placing the facemask without
      having to open and close the Impregum tubes each time. This also
      makes it easier to use smaller amounts of the pastes, which
      results in less waste.

7. Weigh your mice and get set up on each rig, one at time. Record the
   aforementioned variables using your preferred paper or electronic
   documentation method.

   a. Eventually all of this data will be input into the derived
      resources or autoresuscitation plethysmography database. Recording
      at this stage is really only temporary until it is transferred.

Detailed Operations Outline
===========================

1.  Ensure the water bath is on and is set to 35 °C.

    A. Ensure no leaks coming from the water baths.

    B. Ensure all bubbles are removed from each water bath.

    C. Ensure ECG leads of sufficient length are pulled through the
       water bath and not directly in a drip line of water. They must be
       dry at the time of application.

2.  Open git_PCC.

3.  Click *Finish Startup*.

    A. Pay attention to the startup, especially if this is the first
       time that rig has been run that day. Check for:

       i.   Motor function

       ii.  Pipette calibration

       iii. Calibration waveform on GUI

       iv.  Gas valves operational and audible gas exiting when
            challenge gas valve opened.

    B. While Startup is running, you can get all the way through window
       size adjustment and saving the file as you get faster and more
       familiar with the program. Just be sure that you see the
       calibration waveform appear in the GUI before proceeding.

       i. Adjust the window sizes and thresholds as follows:

          1. Windows:

             a. 0.5: Upper window size for Flow

             b. -0.5: Lower window size for Flow

             c. 0.5: Upper window size for ECG

             d. -0.5: Lower window size for ECG

          2. Thresholds:

             a. 0.05: Red line in the Flow to indicate a breath

             b. 0.1: Green line in the flow to indicate breath during
                challenge

             c. 0.14: Red line for ECG window to indicate HR

          3. Other settings

             a. 100 sec.: Calibration duration

             b. 10 sec.: Prefill duration for challenge chamber

             c. Change from pleth filter off (red) to on (green)

                i. **Verify that the respiratory trace is at 0 before
                   turning on the filter. You can adjust this using the
                   knob on the Validyne box.**

4.  Once startup is completed, or during startup if you get fast enough,
    save the file (K).

    A. Make sure to save it to the external SSD

       i.   Go all the way back in the window prompt

       ii.  Media/Pi/PNY SSD/Your_PM_Folder

       iii. Save your file with file name: RUID_date (ex.
            R1156_9-15-2022)

5.  Click the green button (L) to move onto standby phase.

6.  Once the hangar read “Finished Standby”, click (L) again to move
    onto Signal Preview 1.

    A. It is at this point that you can change settings for the
       challenge and timing throughout the experiment.

       i.  Click (M) to change the times for the respective step.

       ii. **DO NOT** hit the step directly otherwise it will transition
           to that step.

7.  Do a quick check at this point to make sure your file is saved as
    you want, and all window, threshold, timing, and challenge settings
    are correct.

8.  Click the green button (L) to move onto calibration.

    A. Complete up to this point on all rigs BEFORE retrieving pups.

9.  Place the prep tray on the first rig you intend to place a mouse on
    an put a small dab of Impregum base paste with a small line of
    Impregum catalyst next to each dab for the number of mice you plan
    to run.

    A. For example, if you plan to run 5 mice, then prepare 5 Impregum
       dabs with catalyst lines on the prep tray before going
       downstairs.

10. Go get pups from downstairs.

11. Immediately begin, one-by-one, weighing and preparing the pups on
    the rigs.

    A. Preparing the pup:

       i.   Mix one of the Impregum paste mounds until you get a purple
            color paste.

       ii.  Apply the paste around the face starting from one eye and
            going in a full circle to the other eye and the top of the
            head.

       iii. Push the facemask onto the pup and hold it there for about
            30 seconds

       iv.  Load the mouse onto the rig, which should be in Signal
            Preview 2.

12. Attach the ECG leads to the back of the pup in the following order:
    Red, white, black

    A. You will need to put a small amount of ECG paste onto the pup for
       each lead.

    B. Trim off the end of the lead to remove the exposed wire from the
       last use..

    C. Strip the end of the wire to reveal fresh wire approximately 1-2
       cm long.

    D. Press the freshly stripped leads into the conductive paste
       applied to the back of the pup.

       i. It is not a bad idea to have a tiny bit of conductive paste on
          the wooden tip while you press these in so you can ensure a
          good connection with the leads.

    E. The best position for the red lead is between the ears.

       i. The higher the better if you are doing intrascapular
          injections.

    F. The white lead should be in the middle of the back.

    G. The black lead should go a little bit above the tail.

    H. Once the leads are providing sufficient ECG traces, apply
       superglue to hold them in place.

       i. It might be easier to just apply the red and black leads
          first, superglue those in place, then attach the white lead
          last.

13. Slide the water bath over the pup, ensure the ECG still looks clean,
    and hit the green button (L).

14. At this point the assay will run by itself and you can monitor via
    VNC.

    A. Additional steps will be required if doing an injection
       experiment. See *injection protocol* to pick up from this point
       with the protocol for injections.

15. Towards the end of Habituation (before starting baseline) it is
    important to double check to make sure the box (N) is green for a
    majority of the time.

    A. If it is red, you will need to go back to Signal Preview 2 and
       adjust the requirements (most likely avg BPM and avg HR) where
       the yellow boxes are (O).

16. When the run is completed, write down the number of episodes and
    click Shutdown.

17. Close the GUI.

18. At the end of the day when all runs are completed, set up a transfer
    of the data you’ve collected from the external hard drive onto the
    brains server into a PM folder that matches the PM you’re saving
    under on the Pi.

Injection Protocol
==================

1. The protocol for injections includes 2 baselines. As default the
   second baseline (after drug administration) is used for injections.
   Therefore, no real requirements or restrictions are set on the first
   baseline.

   A. Thus, it is imperative that you check periodically during the
      initial habituation and baseline to make sure that you are getting
      quality breathing enough to perform calculations on baseline,
      pre-drug levels.

2. Once the animal has gone through baseline, the protocol will stop on
   Inject. It will not advance without input from this point.

   A. Prep your injections in your syringe prior to proceeding.

   B. Pull back the water bath to reveal the animal.

   C. Using flat tweezers, lift the skin between the shoulder blades
      directly up away from the animal.

   D. Into this teepee of skin you’ve created, insert your needle.

      i.   Keep your head directly above the animal as you insert the
           needle to make sure you do not push it through the other
           side.

      ii.  Also make sure to not have the needle going into the head of
           the animal.

      iii. Basically, only insert the tip of the needle in as far as you
           need for the injection to dispense under the skin.

   E. Very slowly inject your drug or placebo.

      i. Do not do this step quickly, because their skin is very thin
         and flimsy and the injected bolus will simply exit the entry
         hole where you put the needle in.

   F. You should see the skin balloon out as you inject. This is a GOOD
      sign.

   G. Remove the needle.

   H. Replace the water bath.

   I. Ensure the ECG and respiratory traces are of equal quality to
      those before the injection.

3. Advance the program from Inject to the next phase of habituation (L).

4. From here, the program will run without need for human intervention.
   You should remain in the room, however, as many errors will require
   you hearing them and intervening, otherwise you will loose the run.

5. When the run is completed, write down the number of episodes and
   click Shutdown.

6. Close the GUI.

7. At the end of the day when all runs are completed, set up a transfer
   of the data you’ve collected from the external hard drive onto the
   brains server into a PM folder that matches the PM you’re saving
   under on the Pi.

Error Reporting
================

For reporting issues and errors with the rigs there are a few things to
keep in mind. Depending on the error, different people with different
backgrounds that may be required to fix the problem. So, it is important
that you record all the information that each of these kinds of people
may need so that sufficient information is available for troubleshooting
and repair.

Standard troubleshooting first step for all kinds of problems: can you
reproduce the error with the eMouse? If so, what are the steps to
reproduce this error?

Below I’ve outlined the various documents and/ or documentation for each
branch of the development team. For every error, it is best practice to
collect ALL of the below items regardless of where you think the error
is derived.

For GitHub migration, tags will be utilized to keep track of engineering
vs. software issues.

8.  Engineers

    A. *Error tracking and reporting back on fixes will be migrated to
       GitHub.*

    B. *Complete an error reporting checklist, which can be found on the
       adjustment clipboards for each rig.*

       i. Include checkboxes for common errors (I.e., missing waveform,
          shaky rig/ fast movement)

    C. *Take notes on the following:*

       i.   Describe the particular piece of the rig involved in the
            failure

       ii.  Describe the failure with as much detail as you can
            (including when during the run the error occurred)

       iii. A picture of the portion of the rig that failed

       iv.  A video of the failure, if possible

       v.   What, if anything, have you done to attempt to fix this
            error?

       vi.  Is the rig no longer functional because of this error? (this
            helps with determining urgency)

9.  Software

    A. *Error tracking and reporting back on fixing errors on GitHub for
       software.*

    B. The .txt and .log files for the run with clear naming

       i.  When you give these to Chris, be sure to include a ReadMe
           document in the folder you choose to share with him that
           outlines what the name of the file is and which error that
           file demonstrates.

       ii. If you use the above convention, as you run in to new or more
           errors, you can simply continue adding files to the same
           shared folder on Box, Dropbox etc. and just update the ReadMe
           file.

    C. A picture of the GUI screen during or just after the error

    D. A text file that contains the contents of the command terminal
       (copy and paste the contents into a text file and save with
       naming convention RUID_date_terminaloutput)

    E. Description of the failure (including when during the run the
       error occurred)

10. General

    A. Has the error occurred previously?

    B. Who else has experienced this error?

    C. Have you noticed anything about the circumstances that stick out?

       i. For example, does it seem to only happen at the end of the
          day, or after another run has occurred prior to this run.

.. figure:: _static/Software_Screen_Picture1.png
   :width: 6.73148in
   :height: 4.12083in
   :alt: Software Screen Picture

   Software Screen Picture
