## Overview
Snapmint is a tool to facilitate live snapshot uploads from a video source, such as a webcam, using opencv, a data subscription source, and a storage bucket. Essentially this program will continually take photos from a connected webcam, store a cache of timestamped photos in memory, listen to external requests for photos at a certain time, and upload those photos as requested.  
  
I am using Google Cloud and Firebase for job subscription and storage, but these could be easily swapped out with other services. The system is designed for a high volume of requests, so everything is processed in batches and multithreading is used to ensure continuous photo capture is uninterrupted by upload tasks.

## Example Use Case
I originally created Snapmint to power a live drawing stream called Sketchbox where an artist is shown sketching and viewers are able to collect a snapshot of the in-progress sketch at any time. They collect a snapshot by minting an NFT, which then triggers a *job* event that instructs Snapmint to capture and upload the requested frame of the artist's in-progress drawing. This image is then attached to the buyer's NFT via a metadata update, made possible by [Transient Labs' ERC-7160 multi-metadata](https://docs.transientlabs.xyz/tl-creator-contracts/erc7160tl) contract.
  
Here are some example outputs:
<p float="left">
  <img src="./assets/1729271724.jpg" width="30%" />
  <img src="./assets/1729271736.jpg" width="30%" />
  <img src="./assets/1729271748.jpg" width="30%" />
</p>


## Additional Use Cases
Although Snapmint was created for this very specific project, I believe it could be used for a variety of other creative projects. With the rise in popularity of live streaming, creators can now further engage viewers by allowing them to capture a certain moment from a stream. The capture source could be a camera, as it is in Sketchbox, but it could also be a continuously changing digital artwork. Anything that is interesting to capture live on a frame-by-frame basic could theoretically be used as an input source to Snapmint.

## Implementation and Usage

If you plan to use Snapmint as I do, with Firebase job documents and Google Cloud Storage, follow these instructions. If not, jump to the **Custom Implementation** section below. There's certainly an opportunity to build this purely using blockchain tools, I just didn't build it that way due to Ensemble's existing infrastructure.

### Prerequisites

1. You need a Google Cloud account with Firebase Firestore and Firebase Storage activated. Tutorials can be found in the [Google Cloud documentation](https://firebase.google.com/docs/firestore/quickstart).
2. If you are planning to use the [Transient Labs ERC-7160 multi-metadata](https://docs.transientlabs.xyz/tl-creator-contracts/erc7160tl) contract, you will need to deploy it and set up a [sale](https://docs.transientlabs.xyz/stacks/stacks-overview).
3. Finally, you will need some infrastructure to watch mint events and create job documents to trigger the Snapmint upload process. My system is described in detail below.

### Install gcloud
The easiest way to read and write to your Google Cloud data locally is by signing into the `gcloud` sdk.
  
**Steps to install the gcloud SDK are available [here](https://cloud.google.com/sdk/docs/install).**

Once you have installed the CLI, run the following commands to login and get your project ID:  

**Login to gcloud:**  
`gcloud auth application-default login`  

**Find and activate your project:**  
`gcloud projects list`  
`gcloud config set project <PROJECT_ID>`  
  
### Activate Python environment and install dependencies

From the project directory, create and activate a virtual environment:  
`python3 -m venv venv`  
`source venv/bin/activate`  

Install project dependencies:  
`pip install -r requirements.txt`

### Set the configuration details

Open the `configuration.py` file and edit the following values:
1. Set the `CONTRACT_ADDRESS` value to your ERC-7160 contract address. This is not technically necessary, but the variable will be used as a folder to store your outputs on disk and in the cloud, ex. `CLOUD_BUCKET/frames/<CONTACT_ADDRESS>`.  
2. Set the `STORAGE_URL` to your cloud storage base URL. This should follow the format `<PROJECT_ID>.appspot.com`.  
3. Depending on how many cameras you have connected to your computer, you may need to adjust the `CAMERA_INDEX` variable.  

### Running the script
From the root of the project directory, run the following command:  
`python src/main.py`  
  
This will immediately start the capture loop, storing frames in a circular memory buffer every `CAPTURE_FREQUENCY` seconds up to `BUFFER_SIZE` frames. Checkpoint frames will also be saved to disk every `CHECKPOINT_FREQUENCY` seconds. Check out these variables, along with other configurations, in `configuration.py`.

To trigger a snapshot upload, create a new document in Firestore in the `jobs` collection with the structure:
```
{
    mediaTimestamp: null,
    dateCreated: number, // unix timestamp in seconds
}
```

## Custom Implementation
If you would like to customize your implementation and avoid using a web2 service like GCP/Firebase, here are some things you will need to change:  
  
### Remove Firebase
First, you can eliminate the Firebase imports and initialization code from `main.py`.  
  
### Use an alternative upload bucket
Next, you can implement your own image upload method. The `upload_frame_to_storage()` method in `outputManager.py` will need to be updated to upload images to your chosen provider. For example, you could upload directly to IPFS or Arweave for decentralized storage.  
  
### Use an alternative job subscription method
Finally, you will need to adjust the job subscription method to watch for new snapshot requests. Take a look at the `fetch_jobs()` method in `subscriptionManager.py` and adjust it to your needs. I would recommend looking into something like [web3.py](https://web3py.readthedocs.io/en/stable/web3.contract.html#events) or [Alchemy](https://docs.alchemy.com/) to query / subscribe to mint events on the ERC-7160 contract.

**Helpful tips**  
* Enable the `IS_MOCK` configuration variable to bypass the camera and create test images with a printed timestamp. I found this very helpful for development and testing.
* If you want to capture a screen recording instead of a camera, look into something like [mss](https://pypi.org/project/mss/) and feed it into cv2.


## System Design
The system consists of four main modules described below. The system is designed for a large volume of job requests, so it avoids any individual subscription-based logic in favor of batch processing. Each module is also run in an independent event loop to ensure processes do not interfere with each other. The highly modular design allows for easy replacement of a specific module for creators who may want a different capture method, job method, or upload method.    

**Capture Manager:**  
This module manages all interfacing with the camera via opencv (cv2). This includes initialization and configuring details including capture resolution and FPS. The module exposes a `perform_capture()` method which immediately captures a frame and performs adjustments based on global config values, such as rotation and flips. The module runs a loop to capture frames every `CAPTURE_FREQUENCY` seconds and add them to the buffer.

It also includes a `mock_read()` method which creates an artificial frame with a random background color and the current time printed in the center.

**Buffer Manager:**  
The buffer manager is a circular (FIFO) buffer to store frames and timestamps in memory. It uses an async lock mechanism to ensure data integrity as the buffer can cycle rapidly when the program is operating - frames may be added up to the maximum frame rate of the camera. The buffer is fairly standard, and it includes a method `find_closest_by_timestamp()` to find the *closest* frame to the request time. For example, if the buffer only holds 1 minute of images and a request comes in for 5 minutes ago, the buffer will return the oldest image available. 

**Tip:** Make sure your buffer size is large enough to hold images until your job requests come in, but not so large that your computer runs out of memory!

**Subscription Manager:**  
This module continually queries Firestore looking for new job documents. The documents must follow the structure defined above. The `dateCreated` value is used by Snapmint to pull the closest available frame from the buffer. The `mediaTimestamp` should be null when the job is pulled down (this is how the query determines if a job has been fulfilled) and it will be updated to the frame timestamp by Snapmint. 

For example, if a job request comes in with a *dateCreated* value of *1730000000*, Snapmint will check the buffer for a frame captured as close to that time as possible. If the closest frame was taken at *1730000001*, that frame will be uploaded to the Google Cloud storage bucket and the job document will be updated with the *mediaTimestamp* set to *1730000001*.

The subscription manager will continually query the database every `BATCH_FREQUENCY` seconds. As mentioned above, you may rip out the Firebase functionality and replace it with a method to directly query the blockchain and find recent mint events.

**Output Manager:**  
The output module handles two core functions: saving checkpoint images to your hard drive and requested images to the cloud. Again, you could choose to rip out the GCP storage uploads and use a different storage provider. All uploads are run in a separate thread to avoid any interruptions to the subscription or capture processes.


## Useful Documentation
**Using Google Cloud services in Python**
* https://cloud.google.com/storage/docs/uploading-objects-from-memory
* https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python
* https://stackoverflow.com/questions/37003862/how-to-upload-a-file-to-google-cloud-storage-on-python-3