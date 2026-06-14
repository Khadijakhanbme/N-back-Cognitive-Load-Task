#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nback_task.py — fNIRS N-back Block Design Experiment
0-back and 2-back conditions, 16 blocks total (8 per condition).
Designed for PsychoPy Standalone v2026.1.1.

Timing architecture follows Oxford N-back (mjcolwell/n-back_oxford):
  - globalClock: absolute time from experiment start (never reset)
  - routineTimer: non-slip duration control (reset per routine)
  - All logged timestamps from globalClock.getTime() after win.flip()

Output:
  data/<participant_id>_<date>.csv        — trial-by-trial data (ExperimentHandler)
  data/<participant_id>_<date>_events.csv — block/rest onsets for fNIRS alignment
"""

import os
import csv
import random
from datetime import datetime
from psychopy import gui, visual, core, data, event

# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    'n_blocks_per_condition': 8,     # 8 x 0-back + 8 x 2-back = 16 blocks total
    'cue_duration': 3.0,             # seconds
    'n_stimuli_per_block': 16,       # 16 x 1.5s = 24s task per block
    'stimulus_duration': 0.5,        # 500 ms
    'isi_duration': 1.0,             # 1000 ms
    'rest_mean': 20.0,               # seconds
    'rest_jitter': 3.0,              # rest ranges 17-23s
    'initial_baseline': 20.0,        # fixation cross at experiment start
    'n_targets_min': 4,              # targets per block (~25-30%)
    'n_targets_max': 5,
    'digits': list(range(10)),       # stimuli: 0-9
    'match_key': 'return',           # Enter/Return key (numpad or main) = match / target
    'nonmatch_key': 'lctrl',         # left Ctrl = nonmatch
    'practice_accuracy_threshold': 0.80,
    'practice_stimuli': 8,           # stimuli per practice block
    'practice_targets': 2,           # targets per practice block
    'feedback_duration': 0.5,        # seconds to show Correct/Incorrect
}

FRAME_TOLERANCE = 0.001  # ~1 ms, less than one 60 Hz frame

# ============================================================
# MODULE-LEVEL GLOBALS (assigned in main())
# ============================================================

win = None
globalClock = None
routineTimer = None
thisExp = None
events_file = None
events_writer = None
events_filename = None
isi_stim = None
experiment_start_time = None  # stores datetime when experiment begins for wall-clock sync

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_escape():
    """Quit without saving files if Escape is pressed.
    Press 'f' to toggle fullscreen mode."""
    keys = event.getKeys()
    if 'escape' in keys:
        if events_file is not None:
            try:
                events_file.close()
            except Exception:
                pass
            try:
                os.remove(events_filename)  # discard partial events file
            except Exception:
                pass
        if thisExp is not None:
            thisExp.abort()   # discards trial CSV (no saveAsWideText called)
        if win is not None:
            win.close()
        core.quit()
    
    # Toggle fullscreen with 'f' key
    if 'f' in keys or 'F' in keys:
        win.fullscr = not win.fullscr



def show_instruction_screen(text_stim, message):
    """Display message and wait for any keypress to continue.
    Press 'f' anytime to toggle fullscreen mode."""
    text_stim.text = message
    event.clearEvents('keyboard')
    while True:
        check_escape()
        text_stim.draw()
        win.flip()
        keys = event.getKeys()
        if keys:
            # Only break if a non-f key was pressed
            if not all(k in ['f', 'F'] for k in keys):
                break


def log_event(block_number, event_type, condition='', detail=''):
    """Write one event row to the fNIRS events CSV.
    event_type: 'baseline_start' | 'cue_start' | 'task_start' | 'task_end' |
                'rest_start' | 'experiment_end'
    condition:  '0-back' | '2-back' | 'baseline' | ''
    detail:     accuracy on task_end (e.g. 'accuracy=87.5'),
                duration on rest_start (e.g. 'duration=19.2')
    """
    # Get relative timestamp (seconds from experiment start)
    rel_timestamp = round(globalClock.getTime(), 4)
    # Get absolute wall-clock timestamp in ISO format (same as sensor data)
    wall_clock = datetime.now().isoformat(timespec='microseconds')
    
    events_writer.writerow([
        rel_timestamp,
        wall_clock,
        block_number,
        event_type,
        condition,
        detail,
    ])
    events_file.flush()

# ============================================================
# SEQUENCE GENERATION
# ============================================================

def generate_2back_sequence(n_stimuli, n_targets, digits):
    """
    Generate a digit sequence with exactly n_targets 2-back matches.
    No accidental extra 2-back matches beyond the intended targets.

    Returns list of dicts: {digit, is_target, correct_response}
    """
    # Choose which positions will be 2-back targets (need at least index 2)
    target_positions = set(random.sample(range(2, n_stimuli), n_targets))

    seq = []
    for i in range(n_stimuli):
        if i in target_positions:
            # Must equal the digit two positions back
            digit = seq[i - 2]['digit']
        else:
            # Must NOT equal the digit two positions back (avoid accidental match)
            forbidden = set()
            if i >= 2:
                forbidden.add(seq[i - 2]['digit'])
            # Also try to avoid 1-back repeats (reduces visual monotony)
            if i >= 1:
                forbidden.add(seq[i - 1]['digit'])

            valid = [d for d in digits if d not in forbidden]
            if not valid:
                # Relax 1-back constraint only — 2-back constraint is non-negotiable
                valid = [d for d in digits if d != seq[i - 2]['digit']]
            digit = random.choice(valid)

        is_target = (i in target_positions)
        seq.append({
            'digit': digit,
            'is_target': is_target,
            'correct_response': CONFIG['match_key'] if is_target else CONFIG['nonmatch_key'],
        })

    return seq


def generate_0back_sequence(n_stimuli, n_targets, target_digit, digits):
    """
    Generate a digit sequence for 0-back where exactly n_targets are
    the pre-specified target_digit.

    Returns list of dicts: {digit, is_target, correct_response}
    """
    target_positions = set(random.sample(range(n_stimuli), n_targets))
    non_target_digits = [d for d in digits if d != target_digit]

    seq = []
    for i in range(n_stimuli):
        if i in target_positions:
            digit = target_digit
            is_target = True
        else:
            digit = random.choice(non_target_digits)
            is_target = False

        seq.append({
            'digit': digit,
            'is_target': is_target,
            'correct_response': CONFIG['match_key'] if is_target else CONFIG['nonmatch_key'],
        })

    return seq

# ============================================================
# BLOCK ORDER GENERATION
# ============================================================

def generate_block_order():
    """
    Create pseudorandomised block order: n x '0-back' + n x '2-back'.
    Constraint: no condition appears more than 2 consecutive times.
    Each 0-back block gets a unique target digit cycling through 0-9.

    Returns list of dicts: {condition, target_digit}
    """
    n = CONFIG['n_blocks_per_condition']
    conditions = ['0-back'] * n + ['2-back'] * n

    # Shuffle+validate: retry until constraint satisfied (typically < 5 tries)
    for _ in range(10000):
        random.shuffle(conditions)
        valid = all(
            not (conditions[i] == conditions[i - 1] == conditions[i - 2])
            for i in range(2, len(conditions))
        )
        if valid:
            break

    result = [{'condition': c, 'target_digit': None} for c in conditions]

    # Assign unique target digits to 0-back blocks (cycle through available digits)
    zeroback_digits = list(CONFIG['digits'])
    random.shuffle(zeroback_digits)
    digit_index = 0
    for block in result:
        if block['condition'] == '0-back':
            block['target_digit'] = zeroback_digits[digit_index % 10]
            digit_index += 1

    return result

# ============================================================
# TIMED ROUTINE FUNCTIONS
# ============================================================

def run_fixation(duration, fixation_stim):
    """Display fixation cross for exactly `duration` seconds (non-slip)."""
    fixation_stim.draw()
    win.flip()
    routineTimer.reset()
    while routineTimer.getTime() < duration - FRAME_TOLERANCE:
        fixation_stim.draw()
        win.flip()
        check_escape()


def run_cue(duration, cue_stim, cue_text):
    """Display cue text for exactly `duration` seconds (non-slip)."""
    cue_stim.text = cue_text
    cue_stim.draw()
    win.flip()
    routineTimer.reset()
    while routineTimer.getTime() < duration - FRAME_TOLERANCE:
        cue_stim.draw()
        win.flip()
        check_escape()


def run_trial(digit_stim, trial_info):
    """
    Run one 1.5s trial: 500ms digit + 1000ms blank.
    Accept return/lctrl response during the full window.

    Returns dict: {stimulus_onset_time, response_key, response_correct, reaction_time}
    """
    trial_duration = CONFIG['stimulus_duration'] + CONFIG['isi_duration']
    response_key = None
    reaction_time = None
    rt_clock = core.Clock()

    # Clear any buffered keypresses from the previous trial/cue
    event.clearEvents('keyboard')

    # First flip: show digit
    digit_stim.text = str(trial_info['digit'])
    digit_stim.draw()
    win.flip()
    stimulus_onset_time = globalClock.getTime()  # after flip = on-screen time
    rt_clock.reset()      # RT measured from stimulus onset
    routineTimer.reset()  # Non-slip duration for this trial

    while routineTimer.getTime() < trial_duration - FRAME_TOLERANCE:
        t = routineTimer.getTime()
        check_escape()

        # Draw digit during stimulus phase, small dot during ISI
        if t < CONFIG['stimulus_duration'] - FRAME_TOLERANCE:
            digit_stim.draw()
        else:
            isi_stim.draw()

        win.flip()

        # Poll keys after flip (catches presses from previous frame)
        if response_key is None:
            keys = event.getKeys(
                keyList=[CONFIG['match_key'], CONFIG['nonmatch_key']],
                timeStamped=rt_clock
            )
            if keys:
                response_key = keys[0][0]
                reaction_time = keys[0][1]

    response_correct = (response_key == trial_info['correct_response'])

    return {
        'stimulus_onset_time': stimulus_onset_time,
        'response_key': response_key,
        'response_correct': response_correct,
        'reaction_time': reaction_time,
    }


def run_practice_trial(digit_stim, feedback_stim, trial_info):
    """
    Run one practice trial (same timing as main trial) then show feedback.
    Returns True if response was correct.
    """
    result = run_trial(digit_stim, trial_info)

    # Show feedback
    if result['response_correct']:
        feedback_stim.text = 'Correct'
        feedback_stim.color = 'green'
    else:
        feedback_stim.text = 'Incorrect'
        feedback_stim.color = 'red'

    feedback_stim.draw()
    win.flip()
    core.wait(CONFIG['feedback_duration'])

    return result['response_correct']

# ============================================================
# PHASE FUNCTIONS
# ============================================================

def run_instruction_screens(text_stim):
    """Show 3 instruction screens, advancing on any keypress."""
    show_instruction_screen(text_stim,
       "Welcome to the N-back Task\n\n"
       "You will see a series of digits on the screen, one at a time.\n"
       "Your task is to respond as quickly and accurately as possible.\n\n"
       "Use the GREEN and RED keys to respond.\n\n"
       "Press 'f' to toggle fullscreen mode.\n\n"
       "Press any key to continue."
    )

    show_instruction_screen(text_stim,
        "0-BACK Task\n\n"
"At the start of each block, a TARGET digit will be shown.\n\n"
"Press the GREEN key if the digit matches the TARGET.\n"
"Press the RED key for all other digits.\n\n"
"Press any key to continue."
    )

    show_instruction_screen(text_stim,
       "2-BACK Task\n\n"
"Press the GREEN key if the current digit matches the digit\n"
"shown TWO trials ago.\n"
"Press the RED key for all other digits.\n\n"
"For the first two digits, always press RED.\n\n"
"Press any key to continue."
    )


def run_practice_phase(digit_stim, feedback_stim, text_stim, cue_stim):
    """
    Adaptive practice:
      0-back: 1 block mandatory; 2nd block only if accuracy < 80%.
      2-back: minimum 2 blocks; 3rd block if accuracy < 80% after block 2;
              if still < 80% after block 3, show review instruction then 1 more block.
    """
    n = CONFIG['practice_stimuli']
    n_tgt = CONFIG['practice_targets']

    # --- 0-back practice ---
    show_instruction_screen(text_stim,
        "PRACTICE -  0-back\n\n"
"Press GREEN if you see the TARGET digit.\n"
"Press RED for all other digits.\n\n"
"Press any key to begin practice."
    )

    for block_num in range(1, 3):  # up to 2 blocks
        target_digit = random.choice(CONFIG['digits'])
        cue_text = f"0-BACK PRACTICE\n\nTarget digit: {target_digit}"
        run_cue(CONFIG['cue_duration'], cue_stim, cue_text)

        sequence = generate_0back_sequence(n, n_tgt, target_digit, CONFIG['digits'])
        n_correct = sum(run_practice_trial(digit_stim, feedback_stim, trial)
                        for trial in sequence)
        accuracy = n_correct / n * 100

        show_instruction_screen(text_stim,
            f"0-back Practice Block {block_num} complete.\n\n"
            f"Accuracy: {accuracy:.0f}%\n\n"
            "Press any key to continue."
        )

        if accuracy >= CONFIG['practice_accuracy_threshold'] * 100:
            break  # passed — skip optional 2nd block

    # --- 2-back practice ---
    show_instruction_screen(text_stim,
        "PRACTICE — 2-back\n\n"
"Press GREEN key if the current digit matches the digit\n"
"shown TWO trials ago.\n"
"Press RED for all other digits.\n\n"
"For the first two digits, always press RED.\n\n"
        "since there is nothing to compare yet.\n\n\n\n"
        "Press any key to begin practice."
    )

    twoback_accuracy = 0
    for block_num in range(1, 4):  # up to 3 blocks
        cue_text = "2-BACK PRACTICE\n\nPress GREEN key for 2-back matches"
        run_cue(CONFIG['cue_duration'], cue_stim, cue_text)

        sequence = generate_2back_sequence(n, n_tgt, CONFIG['digits'])
        results = [run_practice_trial(digit_stim, feedback_stim, trial)
                   for trial in sequence]

        # Exclude first 2 trials from 2-back scoring
        scored = results[2:]
        n_scored = len(scored)
        n_correct_scored = sum(scored)
        twoback_accuracy = (n_correct_scored / n_scored * 100) if n_scored > 0 else 0

        show_instruction_screen(text_stim,
            f"2-back Practice Block {block_num} complete.\n\n"
            f"Accuracy: {twoback_accuracy:.0f}%\n\n"
            "Press any key to continue."
        )

        # After block 2: exit if >= 80%; after block 3: always exit
        if block_num >= 2 and twoback_accuracy >= CONFIG['practice_accuracy_threshold'] * 100:
            break
        if block_num == 3:
            break

    # If still below threshold after 3 blocks: review + 1 more block
    if twoback_accuracy < CONFIG['practice_accuracy_threshold'] * 100:
        show_instruction_screen(text_stim,
            "Let's review the 2-back task\n\n"
            "Press GREEN key if the current digit matches the digit\n"
            "Press RED key for all other digits.\n\n"            "shown TWO trials ago.\n"
            "REMEMBER:\n"
            "For the first two digits, always press RED key.\n\n\n\n"
            "Press any key for one more practice block."
        )
        cue_text = "2-BACK PRACTICE\n\nPress GREEN key for 2-back matches"
        run_cue(CONFIG['cue_duration'], cue_stim, cue_text)

        sequence = generate_2back_sequence(n, n_tgt, CONFIG['digits'])
        results = [run_practice_trial(digit_stim, feedback_stim, trial)
                   for trial in sequence]
        scored = results[2:]
        n_scored = len(scored)
        twoback_accuracy = (sum(scored) / n_scored * 100) if n_scored > 0 else 0

        show_instruction_screen(text_stim,
            f"2-back Practice complete.\n\n"
            f"Accuracy: {twoback_accuracy:.0f}%\n\n"
            "Press any key to continue."
        )

    show_instruction_screen(text_stim,
        "Practice complete!\n\n"
        "The main task will now begin.\n\n\n\n\n"
        "There will be no feedback during the main task.\n\n\n"
        "Press any key when you are ready."
    )


def run_initial_baseline(fixation_stim):
    """Display fixation cross for the initial baseline period."""
    log_event(0, 'baseline_start', 'baseline')
    run_fixation(CONFIG['initial_baseline'], fixation_stim)


def run_block(block_info, block_number, digit_stim, fixation_stim, cue_stim):
    """
    Run one complete block: cue → n_stimuli trials → jittered rest.
    Logs events and saves trial data to thisExp.
    """
    condition = block_info['condition']
    n_targets = random.randint(CONFIG['n_targets_min'], CONFIG['n_targets_max'])

    # Generate stimulus sequence
    if condition == '0-back':
        target_digit = block_info['target_digit']
        sequence = generate_0back_sequence(
            CONFIG['n_stimuli_per_block'], n_targets, target_digit, CONFIG['digits']
        )
        cue_text = f"0-BACK\n\nTarget digit: {target_digit}"
    else:
        sequence = generate_2back_sequence(
            CONFIG['n_stimuli_per_block'], n_targets, CONFIG['digits']
        )
        cue_text = "2-BACK\n\nPress GREEN key for 2-back matches"

    # --- Cue phase ---
    if condition == '0-back':
        log_event(block_number, 'cue_start', condition, f'target={target_digit}')
    else:
        log_event(block_number, 'cue_start', condition)
    run_cue(CONFIG['cue_duration'], cue_stim, cue_text)

    # --- Task phase ---
    log_event(block_number, 'task_start', condition)
    n_correct = 0
    n_correct_scored = 0  # 2-back: excludes first 2 trials
    for trial_number, trial_info in enumerate(sequence, start=1):
        result = run_trial(digit_stim, trial_info)
        if result['response_correct']:
            n_correct += 1
            if condition == '2-back' and trial_number >= 3:
                n_correct_scored += 1

        thisExp.addData('block_number', block_number)
        thisExp.addData('condition', condition)
        thisExp.addData('trial_number', trial_number)
        thisExp.addData('digit', trial_info['digit'])
        thisExp.addData('is_target', int(trial_info['is_target']))
        thisExp.addData('correct_response', trial_info['correct_response'])
        thisExp.addData('stimulus_onset_time', round(result['stimulus_onset_time'], 4))
        thisExp.addData('response_key', result['response_key'] if result['response_key'] else 'none')
        thisExp.addData('response_correct', int(result['response_correct']))
        thisExp.addData('reaction_time',
                        round(result['reaction_time'], 4) if result['reaction_time'] else '')
        thisExp.nextEntry()

    # --- Rest phase ---
    if condition == '2-back':
        scored_n = CONFIG['n_stimuli_per_block'] - 2
        block_accuracy = round(n_correct_scored / scored_n * 100, 1)
    else:
        block_accuracy = round(n_correct / CONFIG['n_stimuli_per_block'] * 100, 1)

    rest_duration = (CONFIG['rest_mean'] +
                     random.uniform(-CONFIG['rest_jitter'], CONFIG['rest_jitter']))
    log_event(block_number, 'task_end', condition, f'accuracy={block_accuracy}')
    log_event(block_number, 'rest_start', 'rest', f'duration={round(rest_duration, 1)}')

    # Show accuracy for first 2.0s of rest (colour-coded), then plain fixation
    cue_stim.color = 'green' if block_accuracy >= 80 else ('yellow' if block_accuracy >= 60 else 'red')
    cue_stim.text = f'Block {block_number} ({condition}) complete\nAccuracy: {block_accuracy:.0f}%'
    cue_stim.draw()
    win.flip()
    routineTimer.reset()
    while routineTimer.getTime() < 2.0 - FRAME_TOLERANCE:
        cue_stim.draw()
        win.flip()
        check_escape()
    cue_stim.color = 'white'  # reset for next cue

    run_fixation(rest_duration - 2.0, fixation_stim)
    log_event(block_number, 'rest_end', 'rest')

# ============================================================
# MAIN
# ============================================================

def main():
    global win, globalClock, routineTimer, thisExp, events_file, events_writer, events_filename, isi_stim, experiment_start_time

    # --- Participant dialog (must run BEFORE visual.Window) ---
    exp_info = {'participant_id': '', 'session': '1'}
    dlg = gui.DlgFromDict(dictionary=exp_info,
                          title='N-back Task',
                          order=['participant_id', 'session'])
    if not dlg.OK:
        core.quit()

    date_str = data.getDateStr()  # e.g. '2026_Mar_19_1430'

    # --- Data directory and file paths ---
    os.makedirs('data', exist_ok=True)
    base_filename = os.path.join(
        'data', f"{exp_info['participant_id']}_{date_str}"
    )
    events_filename = base_filename + '_events.csv'

    # --- ExperimentHandler (explicit save only — prevents duplicate files) ---
    thisExp = data.ExperimentHandler(
        name='nback_fNIRS',
        version='1.0',
        extraInfo=exp_info,
        runtimeInfo=None,
        originPath=__file__,
        savePickle=False,
        saveWideText=False,
        dataFileName=base_filename,
    )
    thisExp.dataNames = []  # Prevent default empty columns

    # --- Events CSV ---
    events_file = open(events_filename, 'w', newline='', encoding='utf-8')
    events_writer = csv.writer(events_file)
    events_writer.writerow(['timestamp_relative', 'timestamp_wall_clock', 'block_number', 'event_type', 'condition', 'detail'])
    events_file.flush()

    # --- Window ---
    win = visual.Window(
        size=[1280, 720],
        fullscr=False,
        color='black',
        units='height',
        allowGUI=True,
        screen=0,
    )
    win.mouseVisible = False

    # --- Clocks ---
    globalClock = core.Clock()   # never reset — absolute time from here
    experiment_start_time = datetime.now()  # wall-clock time for sensor sync
    routineTimer = core.Clock()  # reset before each timed routine

    # --- Stimuli ---
    # Large centred stimulus for digits
    digit_stim = visual.TextStim(
        win, text='', color='white', height=0.15,
        bold=True, pos=(0, 0),
    )
    # Fixation cross (rest / baseline periods)
    fixation_stim = visual.TextStim(
        win, text='+', color='gray', height=0.08, pos=(0, 0),
    )
    # Small dot shown during ISI between trials (· = middle dot)
    isi_stim = visual.TextStim(
        win, text='\u00b7', color='gray', height=0.04, pos=(0, 0),
    )
    # Cue text (slightly smaller to fit two lines)
    cue_stim = visual.TextStim(
        win, text='', color='white', height=0.07,
        wrapWidth=1.5, pos=(0, 0),
    )
    # Instruction / general text
    text_stim = visual.TextStim(
        win, text='', color='white', height=0.05,
        wrapWidth=1.5, pos=(0, 0),
    )
    # Feedback (colour set per trial)
    feedback_stim = visual.TextStim(
        win, text='', color='white', height=0.08, pos=(0, 0),
    )

    # --- Instructions ---
    run_instruction_screens(text_stim)

    # --- Practice ---
    run_practice_phase(digit_stim, feedback_stim, text_stim, cue_stim)

    # --- Initial baseline ---
    run_initial_baseline(fixation_stim)

    # --- Generate block order ---
    block_order = generate_block_order()

    # --- Log block order to events CSV for reference ---
    for i, block in enumerate(block_order, start=1):
        if block['condition'] == '0-back':
            log_event(i, 'block_order', block['condition'], f'target={block["target_digit"]}')
        else:
            log_event(i, 'block_order', block['condition'])

    # --- Main task loop ---
    for block_number, block_info in enumerate(block_order, start=1):
        run_block(block_info, block_number, digit_stim, fixation_stim, cue_stim)

    log_event(0, 'experiment_end')

    # --- End screen ---
    end_stim = visual.TextStim(
        win, text='Experiment complete.\nThank you!',
        color='white', height=0.07, pos=(0, 0),
    )
    end_stim.draw()
    win.flip()
    core.wait(4.0)

    # --- Save and quit ---
    events_file.flush()
    events_file.close()
    thisExp.saveAsWideText(base_filename + '.csv')
    win.close()
    core.quit()


if __name__ == '__main__':
    main()
