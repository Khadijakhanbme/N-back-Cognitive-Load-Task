# N back Cognitive Load Task for fNIRS Study

A PsychoPy implementation of a block-design N-back working memory task developed for functional Near-Infrared Spectroscopy (fNIRS) experiments.

The paradigm was developed for evaluating a wearable multimodal forehead-mounted fNIRS sensor during cognitive workload induction.

---

## Overview

The N-back task is a well-established cognitive paradigm widely used to investigate working memory and prefrontal cortex activation. This implementation includes:

- 0-back (control condition)
- 2-back (working memory condition)
- Adaptive practice phase
- Pseudorandomized block design
- Trial-by-trial behavioural recording
- High-precision event logging for fNIRS synchronization
- Performance feedback between blocks
- Automated generation of behavioural and event log files

The task was designed specifically for fNIRS studies targeting prefrontal cortex activity and cognitive workload assessment.

---

## Validation

Prior to deployment with the custom wearable fNIRS sensor, the paradigm was validated using the Artinis Frontal BriteLite system.

Rest periods served as baseline, the 0-back condition represented low cognitive load, and the 2-back condition represented higher working memory load. The paradigm elicited the expected bilateral prefrontal haemodynamic activation, with stronger activation during 2-back compared to both rest and 0-back conditions, confirming its suitability for cognitive workload and fNIRS studies.

This validation confirmed that the implemented timing parameters, block structure, and task demands were sufficient to reliably elicit cognitive-load-related haemodynamic responses.

---

## Experimental Paradigm

The experiment consists of:

- 8 × 0-back blocks
- 8 × 2-back blocks
- 16 task blocks in total
- Pseudorandomized block order
- No condition appears more than twice consecutively

### Block Structure

<img width="1101" height="617" alt="task paradigm" src="https://github.com/user-attachments/assets/d71420b8-077c-4c5e-82aa-c47c726fdceb" />

---

## Task Conditions

### 0-Back (Control Condition)

A target digit is presented at the start of each block.

Participants press:

- Match key when the displayed digit equals the target digit
- Non-match key for all other digits

This condition primarily measures sustained attention and response execution while minimizing working memory demand.

### 2-Back (Working Memory Condition)

Participants press the match key when the current digit matches the digit presented two trials earlier.

Example:

Sequence:

3 → 7 → 3 → 5 → 5

The third digit ("3") is a target because it matches the digit presented two trials earlier.

The first two stimuli in each 2-back block have no valid reference and are always treated as non-targets.

---

## Timing Parameters

<img width="880" height="306" alt="image" src="https://github.com/user-attachments/assets/d752bd3f-41d3-49d4-a634-09db5780e951" />

---

## Practice Phase

### 0-Back Practice

- One mandatory practice block
- Additional block if accuracy < 80%

### 2-Back Practice

- Minimum of two practice blocks
- Additional practice provided if accuracy remains below 80%
- Trial-by-trial feedback is shown during practice

No feedback is provided during the main experiment.

---

## Behavioural Data Recorded

For each trial the following information is saved:

- Block number
- Condition
- Trial number
- Presented digit
- Target status
- Correct response
- Participant response
- Response accuracy
- Reaction time
- Stimulus onset time

---

## fNIRS Event Logging

A dedicated event log is automatically generated for synchronization with physiological recordings.

Logged events include:

- Baseline start
- Cue start
- Task start
- Task end
- Rest start
- Rest end
- Block order
- Experiment end

Each event contains:

- Relative timestamp
- Wall-clock timestamp
- Block number
- Condition
- Additional metadata

This allows precise alignment with fNIRS acquisition systems during offline analysis.

---

## Output Files

### Behavioural Data

```
participantID_date.csv
```

Contains trial-level behavioural performance.

### Event Log

```
participantID_date_events.csv
```

Contains block and event timing information for synchronization with fNIRS recordings.

---

## Requirements

- Python 3.x
- PsychoPy 2026.1.1 or newer

Install PsychoPy:

```bash
pip install psychopy
```

---

## Running the Task

```bash
python n_back_task.py
```

Participants are prompted for:

- Participant ID
- Session Number

The experiment then proceeds through:

1. Instructions
2. Practice
3. Baseline
4. Main Task
5. End Screen

---

## Research Context

This task was developed within the Electronics and Informatics Department (ETRO), Vrije Universiteit Brussel (VUB), as part of a Master's Thesis investigating wearable multimodal fNIRS sensing for cognitive workload monitoring.

The paradigm was designed to provide robust and reproducible working-memory-related haemodynamic responses suitable for both sensor validation and future cognitive neuroscience applications.

---

## Future Work

The task is intended for use with:

- Wearable fNIRS systems
- Multimodal sensing platforms
- Cognitive workload estimation
- Brain-computer interface research
- Real-world neuroergonomics studies

---
