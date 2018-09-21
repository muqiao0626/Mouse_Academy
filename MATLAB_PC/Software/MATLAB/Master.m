%{
//// Copyright (C) 2018 Meister & Perona Lab at Caltech 
//// -----------------------------------------------------
//// This program is free software: you can redistribute it and/or modify
//// it under the terms of the GNU General Public License as published by
//// the Free Software Foundation, either version 3 of the License, or
//// (at your option) any later version.
////
//// This program is distributed in the hope that it will be useful,
//// but WITHOUT ANY WARRANTY; without even the implied warranty of
//// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
//// GNU General Public License for more details.
////
//// You should have received a copy of the GNU General Public License
//// along with this program. If not, see <http://www.gnu.org/licenses/>.
%}

%% Initialization
s = serial('COM3');
set(s,'BaudRate',9600);

try
    fopen(s);
catch err
    fclose(instrfind);
    error('Make sure you select the correct COM Port where the Arduino is connected.');
end

masterpath = 'C:\Users\MQ_behaivorbox\Documents\MATLAB\'; % Master file path
videopath = 'G:\MouseAcademy1_201807\'; % Video file path
videowindow = [0 10 800 640];
formatOut = 'yyyymmddTHHMMSS';
filename = datestr(now,formatOut);

while (1)

    [t,count1,msg1] = fscanf(s, '%d');
    while (strcmp(msg1, '') == 0)
        [t,count1,msg1] = fscanf(s, '%d');
    end
    [m,count2,msg2] = fscanf(s);
    while (strcmp(msg2, '') == 0)
        [m,count1,msg2] = fscanf(s);
    end
    
    if (count1 > 5)
        break;
    end
    if (count2 < 5)
        break;
    end
    
    if (t < 0)
        display(m);
        error('Error from Arduino!');
    end
    
    
    format shortg;
    c = clock;
    
    for k = 1:6
        if (Boredness(k) > 0)
            if (etime (c, BorednessTimer(k,:))/3600 > 0) % the hours (replace 0 with your number) the animal is banned from entering the training box if not finishing a session
                Boredness(k) = Boredness(k) - 1;
                BorednessTimer(k,:) = c;
            end
        end
    end   
    
    if (Boredness(t) < 1)
        fprintf(s,'%c','2');
           
        %% Entering
        i = i+1;
    
        [t,count1,msg1] = fscanf(s, '%d');
        while (strcmp(msg1, '') == 0)
            [t,count1,msg1] = fscanf(s, '%d');
        end
        [m,count2,msg2] = fscanf(s);
        while (strcmp(msg2, '') == 0)
            [m,count2,msg2] = fscanf(s);
        end

        if (count1 > 5)
            break;
        end
        if (count2 < 5)
            break;
        end
        
        if (t < 0)
            display(m);
            error('Error from Arduino!');
        end

        format shortg;
        c = clock;

        C = [C; c];
        Tag = [Tag; t];
        M{i} = m;

        AnimalID = ['Animal' num2str(t)];
        TheProtocol = P{t};
        Prot{i} = TheProtocol;
        
        formatOut = 'yyyymmddTHHMMSS';
        timestamp = datestr(now,formatOut);
        videoname = [AnimalID '_' TheProtocol '_' timestamp];
        videofilename = [videopath videoname];
        vid = Startvideorecording(videofilename, videowindow);
        pause(0.5);
        
        display (c);
        display (AnimalID);
        display (m);
        display (TheProtocol);

        idx = find(strcmp([ProtocolFiles(:,1)], TheProtocol));
        low = ProtocolFiles{idx, 2};
        high = ProtocolFiles{idx, 3};
        MaxTrials = ProtocolFiles{idx, 4};

        if (Boredness(t) < 1)
            [status, performance, reward] = RunProtocolforTraining(AnimalID, TheProtocol, MaxTrials); % MaxTrials = 500
        else
            status = -1; performance = 0.6; reward = 0; %Double Check: Shouldn't be -1
        end

        S = [S; status];
        Perf = [Perf; performance];
        RW = [RW; reward];

        display (status);
        display (performance);
        display (reward);

        if (performance >= high)
            P{t} = ProtocolFiles{idx+1, 1};
        elseif (performance < low)
            P{t} = ProtocolFiles{idx-1, 1};
        end

        save([masterpath filename '.mat'],'C','Tag','M','Prot','S','Perf','RW', 'P', 'i', 'Boredness', 'BorednessTimer');

        %% Leaving
        i = i+1;
        
        Endvideorecording(vid);

        fprintf(s,'%c','0');

        [t,count1,msg1] = fscanf(s, '%d');
        while (strcmp(msg1, '') == 0)
            [t,count1,msg1] = fscanf(s, '%d');
        end
        [m,count2,msg2] = fscanf(s);
        while (strcmp(msg2, '') == 0)
            [m,count2,msg2] = fscanf(s);
        end

        if (count1 > 5)
            break;
        end
        if (count2 < 5)
            break;
        end

        format shortg;
        c = clock;

        C = [C; c];
        Tag = [Tag; t];
        M{i} = m;
        Prot{i} = TheProtocol;
        S = [S; status];
        Perf = [Perf; performance];
        RW = [RW; reward];

        if (t < 0)
            display(m);
            error('Error from Arduino!');
        end
        
        if (status == 0)
            BorednessTimer(t,:) = c;
            Boredness(t) = Boredness(t) + 1;
        end
        
        for j = 1:6
            if (Boredness(j) > 1)
            Boredness(j) = 1;
            end
            if (Boredness(j) < 0)
            Boredness(j) = 0;
            end
        end
        
        display (c);
        display (AnimalID);
        display (m);
        display (Boredness);
        display (BorednessTimer);

        save([masterpath filename '.mat'],'C','Tag','M','Prot','S','Perf','RW', 'P', 'i', 'Boredness', 'BorednessTimer');
    
    else
        fprintf(s,'%c','1');
    end
end

fclose(s)
delete(s)
clear s