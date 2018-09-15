function vid = Startvideorecording(filename, window)

%%
vid = videoinput('winvideo', 1, 'MJPG_1280x720');
src = getselectedsource(vid);

%% Set up parameters here
src.Exposure = -6;
vid.ROIPosition = window;
src.Sharpness = 4;

vid.FramesPerTrigger = Inf;

vid.LoggingMode = 'disk';
diskLogger = VideoWriter(filename, 'Archival');

vid.DiskLogger = diskLogger;
diskLogger.FrameRate = 30;
diskLogger.LosslessCompression = true;

%%
preview(vid);
start(vid);

