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

function AveRate = AvePerformance(TrialTypes, Data)
global BpodSystem

Outcomes = zeros(1,Data.nTrials);
for x = 1:Data.nTrials
    if ~isnan(Data.RawEvents.Trial{x}.States.Drinking(1))
        Outcomes(x) = 1;
    elseif ~isnan(Data.RawEvents.Trial{x}.States.Punish(1))
        Outcomes(x) = 0;
    elseif ~isnan(Data.RawEvents.Trial{x}.States.RewardEarlyWithdrawal(1))
        Outcomes(x) = 0;
    else
        Outcomes(x) = 0;
    end
end

L = length(Outcomes);
Catch = sum(Outcomes);

AveRate = Catch/L;

end
