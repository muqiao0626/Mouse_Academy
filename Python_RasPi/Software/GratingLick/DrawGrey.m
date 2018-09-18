function window = DrawGrey(window, grey, windowRect)

screenNumber = max(Screen('Screens'));

% Define black, white and grey
white = WhiteIndex(screenNumber);
grey = white / 2;
[screenXpixels, screenYpixels] = Screen('WindowSize', window);
Screen FillRect?
windowRect = [0 0 screenXpixels, screenYpixels];
window
grey
windowRect
Screen('FillRect', window, grey, windowRect);
return;
end
