# CapCut photo preparation with Ken Burns

Use scripts/prepare_capcut_photos.py to prepare a photo B-roll library through the
local ffmpeg-skill helpers. It orchestrates probe.py, insert.py and look.py; it
does not write raw FFmpeg commands.

## Workflow

1. Discover photos with dry-run.
2. A human or visual agent inspects each useful candidate, identifies the subject,
   chooses a safe 16:9 crop, and records a movement.
3. Use ZOOM_IN or ZOOM_OUT by default. Use PAN_LEFT_ZOOM or PAN_RIGHT_ZOOM only
   when the subject remains visible throughout the full movement.
4. Execute with the reviewed decisions JSON.
5. Inspect every contact sheet before approval.

The wrapper deliberately does not implement face detection, visual subject detection,
automatic crop selection, or aesthetic QA.

## Command

    python scripts/prepare_capcut_photos.py --episode personajes/Nombre/EP0005_Nombre --dry-run

After visual review:

    python scripts/prepare_capcut_photos.py --episode personajes/Nombre/EP0005_Nombre --decisions decisions.json --duration 5

Optional arguments are --source path/to/images and --ffmpeg-skill-dir path/to/ffmpeg-skill.
The default source is 04_IMAGES. The generated structure is:

    09_PROJECT/CAPCUT_READY/KEN_BURNS_LIBRARY/
      01_CLIPS/
      02_CONTACT_SHEETS/
      03_MANIFEST/

## Decisions JSON

    {
      "decisions": [
        {
          "source": "FER_001.jpg",
          "status": "INCLUDE",
          "asset_name": "FERRUCCIO_WORKSHOP",
          "movement": "ZOOM_IN",
          "subject": "Ferruccio and the engine",
          "crop_notes": "Centered 16:9 crop; faces remain fully visible.",
          "notes": "No pan: the edge composition is unsafe."
        },
        {
          "source": "vertical_portrait.jpg",
          "status": "EXCLUDE",
          "notes": "A safe 16:9 crop would cut the face."
        }
      ]
    }

Mechanical exclusions cover character cards, obvious branding/logo assets, and files
under a Kling directory. They never replace human editorial judgment. The wrapper
never overwrites source images and writes a CSV manifest for planned/generated assets
and exclusions.
