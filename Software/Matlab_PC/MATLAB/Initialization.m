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

close all; clear all;

bpod;

C = []; %clock
Tag = [];   %Tag or Error
M = {}; %Message
S = []; %status
Perf = []; %performance
RW = []; %reward
Prot = {}; %protocol

P = cell(6, 1);
for i = 1:6
    P{i} = 'Operant'; %here is for the initial protocol
end
ProtocolFiles = importfile('ProtocolFiles.xlsx');

i = 0;

Boredness = [0 0 0 0 0 0];

BorednessTimer = zeros(6);