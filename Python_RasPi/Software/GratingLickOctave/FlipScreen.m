function flipTime = FlipScreen(window)


% Flip to the screen
flipTime = Screen('Flip', window);

imageArray=Screen('GetImage', window);
imwrite(imageArray, '/home/pi/Mouse_Academy/Python_RasPi/Software/GratingLick/grating.png');

return;
end
