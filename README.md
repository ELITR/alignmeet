# ALIGNMEET
## A Comprehensive Tool for Meeting Annotation, Alignment, and Evaluation

# Installation

## Prerequisites 
### Windows 
- install Python >=3.6
	https://www.python.org/downloads/

- install VLC (install matching version with your system, i.e., x64 or x86):

	VLC x86:
	https://get.videolan.org/vlc/3.0.16/win32/vlc-3.0.16-win32.exe

	 VLC x64:
	https://get.videolan.org/vlc/3.0.16/win64/vlc-3.0.16-win64.exe

- in order to run the program from the command line, make sure you have Python Scritp folder in your PATH, e.g.:

~~~
C:\Users\USER_NAME\AppData\Roaming\Python\Python39\Scripts
~~~

### Linux
Install the latest version of VLC:
~~~
apt-get update && apt-get install ffmpeg vlc
~~~

## Pip

Use this installation mode if you want the latest released version from PyPI:
~~~
pip install alignmeet
~~~

## Updating 

~~~
pip install --upgrade alignmeet
~~~


# User guide

## Running ALIGNMEET

Just open a command line or type <kbd>Windows</kbd> + <kbd>R</kbd> on Windows and type `alignmeet`.

## Creating a new meeting

Go `File → New` (or just type <kbd>Ctrl</kbd> + <kbd>N</kbd>) and go to the folder where the meetings are stored. By left-clicking in this folder, you can create a new empty folder. Name this folder according to the meeting’s name. After you create the new empty folder, select it. The program creates a structure for the meeting:

-   `./` (root folder)
    

    -   You can place a recording of the meeting in any reasonable format supported by VLC (can be either audio or video)
    

-   `transcripts`
    

    -   Each file in this folder is a transcript.
        
    -   Transcript file is a plain text file.
        
    -   If you have an existing transcript, just copy & paste it to this folder. Additionally, if the file comes with DAs annotated with speakers (speaker must be annotated at the beginning of the line in brackets, e.g., (Speaker) ), the program will extract this information.
        
    -   Format of a DA:
    

        -   A semicolon-separated, one DA per line
            
        -   DA;SPEAKER;START_IN_S;END_IN_S
    

-   `minutes`
    

    -   Summaries/Minutes are stored in plaintext files, each minute per line.
        
    -   Other information regarding the meeting can be included in this file in any (plaintext) form (e.g., annotator name, attendees, date, purpose of the meeting, …).
    

-   `annotations`
    

    -   Pairing between summaries/minutes and transcripts.
        
    -   For specific transcript-minutes pair there is a file with the name “{transcript_file}+{minutes_file}”
        
    -   Each file has 3 columns: DA ID, minute ID and Problem
        
    -   The second and third column can contain “None” value (i.e., when either minute or problem is selected only)

## Opening an existing meeting

Go `File → Open` (or just type <kbd>Ctrl</kbd> + <kbd>O</kbd>) and select the root folder of a meeting. It will show you the meeting summary and transcript to annotate.

# User guide for annotation

## Program layout

![Layout](documentation/layout.png)


- A. Transcript panel
- B. Summary panel
- C. Other annotations (e.g., problems like incomprehensible speech or small talk)
- D. Meeting recording playback

## Alignment annotation

![Alignment](documentation/alignment.png)

-   Select a single DA (dialogue act = one numbered line in the transcript) by clicking on it, or select multiple DAs by press-and-hold (or Shift and clicking). To pair the selected DA(s) to a summary unit, double click on the corresponding line in the Summary panel (B). The pairing is represented by the corresponding background colors of the DAs and summary units.
    
-   Similarly, to mark a DA(s) with a problem, select the DA(s) as previously discussed and double click on a problem (C). The annotated problem will be in the right “Problem” column.
     
## Altering the annotation


![Reset](documentation/reset.png)

- You can select DA(s) and pair them with another summary unit/problem.
- Or you can reset selected option, just click the right mouse button. From the context menu choose the option `Reset minutes` or `Reset problems` (you can also use the shortcuts displayed in the context menu).
    

## Edit transcript

![Edit transcript](documentation/edit_transcript.png)

It is possible to make changes in the transcribed text after you select an option Edit transcript shown in the picture. For inserting/deleting use right mouse button and choose an appropriate option from the shown context menu


##  Altering summary

 
![Edit summary](documentation/edit_summary.png)   

Editing of the summary is possible the same way as in the transcript, for inserting/deleting or indenting to the right/left use right mouse button and choose an appropriate option from the shown context menu


##  Problems/Other

You can annotate DA(s) with a problem from a panel `Other`.

We distinguish four types of typical cases when the DA(s) cannot be easily aligned to a summary unit. This list can be changed if needed. We plan to make this list editable by the user.

-   Organizational
    

	-   Parts related to the organization of the meeting or project itself.
    
	-   E.g., information about the present or missing participants at the meeting, or sentences like:
    
		~~~
		"Okay, I’ll write it to the agenda''

		"So that’s resolved and now, we can continue because time is really running"
		~~~


-   Speech incomprehensible
	-   If you don’t understand what was said.
    

-   See separate comment
	-   If nothing from the other options is concise enough, please select it as See separate comment and write your note to the corresponding part to Anna Nedoluzhko <nedoluzko@ufal.mff.cuni.cz>
    

-   Small talk
	-  For parts non-related to the minutes or organization of the meeting or the project itself (e.g., I noticed some topics about Covid and so on…)

4.  Recording/Video


![Playback](documentation/playback.png)   

If the meetings has a recording you can use playback panel. You can use the panel, main menu `Playback` or keyboard shortcuts (see the actual shortcuts in the main menu).

## Git integration

To distribute and synchronize annotation among annotators, you can use Git integration. ALIGNMEET can pull and push changes to a given Git repository.

After the setup, user/annotator just clicks File -> Open repository (`Ctrl + G`). The tool pulls the recent version of the repository and opens a dialog window to select a meeting (the repository might contain more meetings). 

To commit the changes, go File -> Save (`Ctrl + S`). The tool saves the changes to the local copy and pushes them as a new commit to the remote repository. The `Annotator name` in Settings is used as a commit message.

### Setup

Install Git client on the annotator's computer and include it in the `PATH` variable.

You can use any remote Git repository. The repository might contain one or more meetings. If you have more meetings, create a folder per meeting. 

Each annotator must fill these settings:

![Git settings](documentation/git_settings.png)  

| Setting        | Description                                    |
|----------------|------------------------------------------------|
| Annotator name | will be used as commit message                 |
| Repo location  | the location of the local copy                 |
| Repository     | link to Git repository                         |
| Repo user      | Git user with R/W access to the repository     |
| Repo token     | Personal access token for the user (see below) |

#### Personal access token

The Git user that will have R/W access to the repository must create a Personal access token.

In Github go to Settings -> Developer settings -> Personal access tokens -> New personal access token.
Set a note and set an expiration date. Copy the token and distribute it to the annotators. You might want to create a separate token per annotator, so you can revoke individual annotator access. You might also want to create a separate Git user for security reasons.