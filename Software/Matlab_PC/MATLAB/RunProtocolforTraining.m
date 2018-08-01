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

function [status, performance, reward] = RunProtocolforTraining(AnimalID, TheProtocol, MaxTrials)
global BpodSystem

training(AnimalID, TheProtocol);

if (BpodSystem.Data.nTrials == MaxTrials)
    status = 1; % Complete
    performance = AvePerformance(BpodSystem.Data.TrialTypes, BpodSystem.Data);
    reward = BpodSystem.PluginObjects.TotalRewardDelivered;
else
    status = 0; % Not complete
    performance = 0.6; % 60 Percent as a threshold
    reward = BpodSystem.PluginObjects.TotalRewardDelivered;
end

        if ~isempty(BpodSystem.Status.CurrentProtocolName)
            disp(' ')
            disp([BpodSystem.Status.CurrentProtocolName ' ended.'])
        end
        rmpath(fullfile(BpodSystem.Path.ProtocolFolder, BpodSystem.Status.CurrentProtocolName));
        BpodSystem.Status.BeingUsed = 0;
        BpodSystem.Status.CurrentProtocolName = '';
        BpodSystem.Path.Settings = '';
        BpodSystem.Status.Live = 0;
        if BpodSystem.EmulatorMode == 0
            BpodSystem.SerialPort.write('X', 'uint8');
            pause(.1);
            nBytes = BpodSystem.SerialPort.bytesAvailable;
            if nBytes > 0
                BpodSystem.SerialPort.read(nBytes, 'uint8');
            end
            if isfield(BpodSystem.PluginSerialPorts, 'TeensySoundServer')
                TeensySoundServer('end');
            end   
        end
        BpodSystem.Status.InStateMatrix = 0;
        % Shut down protocol and plugin figures (should be made more general)
        try
            Figs = fields(BpodSystem.ProtocolFigures);
            nFigs = length(Figs);
            for x = 1:nFigs
                try
                    close(eval(['BpodSystem.ProtocolFigures.' Figs{x}]));
                catch
                    
                end
            end
            try
                close(BpodNotebook)
            catch
            end
        catch
        end
        set(BpodSystem.GUIHandles.RunButton, 'cdata', BpodSystem.GUIData.GoButton, 'TooltipString', 'Launch behavior session');
        if BpodSystem.Status.Pause == 1
            BpodSystem.Status.Pause = 0;
        end
        % ---- end Shut down Plugins
end