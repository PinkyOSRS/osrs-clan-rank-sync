# GitHub Setup Instructions

Follow these steps to set up your clan rank processor on GitHub:

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in (or create an account if needed)
2. Click the "+" icon in the top right and select "New repository"
3. Name your repository (e.g., "clan-rank-processor")
4. Make it public (or private if you prefer)
5. Click "Create repository"

## Step 2: Upload the Files

1. In your new repository, click "uploading an existing file"
2. Upload all the files from this `github-setup` folder, maintaining the same directory structure
3. Commit the changes

## Step 3: Create the Uploads Folder

1. In your repository, click "Add file" > "Create new file"
2. In the name field, type "uploads/README.md"
3. In the content area, add: "Upload clan rank JSON files to this folder"
4. Commit the new file

## Step 4: Test the Workflow

1. Go to the "uploads" folder
2. Click "Add file" > "Upload files"
3. Upload the sample-upload.json file provided
4. Commit the changes
5. Go to the "Actions" tab to see your workflow running
6. After the workflow completes, check that clan_ranks_for_bot.json appears in your main directory

## Step 5: Connect Your Discord Bot

Update your Discord bot to fetch the data from:
```
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO_NAME/main/clan_ranks_for_bot.json
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name.

## How to Use Going Forward

Whenever a clan admin needs to upload a new clan rank file:
1. They go to the repository's "uploads" folder
2. Click "Add file" > "Upload files"
3. Upload the JSON file
4. The system automatically processes it and updates clan_ranks_for_bot.json