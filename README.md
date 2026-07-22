# DayMap

DayMap is a simple daily planner I made using Python and Streamlit. It helps me organize my task and plan my day effectively.

## Features

- Add, edit, complete and delete tasks
- Set dates, times, and priorities
- View upcoming and completed tasks
- Create a daily schedule

## Why I made this

I made DayMap to keep me on schedule as I think I have a lot of things to do.

Thanks, try it out [here]()

## Deployment 
### Deployment Guide

I deployed this project using AI assistance and learned valuable lessons along the way. Here's how to replicate the setup:

DayMap uses two services. Render hosts the Streamlit app because Streamlit needs *WebSockets*. Vercel only hosts the loading page.

1. Deploy `srinivasagudi0/Day-Planner` to Render first. Render will read `render.yaml` and start the app with the included Streamlit command.
2. Copy the Render URL after the deployment is live.
3. Import `srinivasagudi0/Day-Planner` into Vercel.
4. Set the Vercel **Root Directory** to `vercel-loader`.
5. Add a Vercel environment variable named `DAYMAP_APP_URL` and set it to the Render URL.
6. Deploy the Vercel project. If the environment variable is changed later, redeploy it.

The loading page calls `/api/health`, which checks Render's `/_stcore/health` endpoint. It keeps checking while Render starts, then sends the visitor to DayMap when the app is ready.


I am very excited to get this reviewed and hope you like it.