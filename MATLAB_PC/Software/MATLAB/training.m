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

function training(AnimalID, TheProtocol)

global BpodSystem

%% Populate UI
BpodSystem.Path.ProtocolFolder = BpodSystem.SystemSettings.ProtocolFolder;

BpodSystem.GUIData.DummySubjectString = AnimalID;  %Here to enter the animal ID

%% Here to enter the protocol  
SelectedProtocolName = TheProtocol;

BpodSystem.Status.CurrentProtocolName = SelectedProtocolName;
DataPath = fullfile(BpodSystem.Path.DataFolder,BpodSystem.GUIData.DummySubjectString);
ProtocolName = BpodSystem.Status.CurrentProtocolName;

% Make standard folders for this protocol.  This will fail silently if the folders exist
mkdir(DataPath, ProtocolName);
mkdir(fullfile(DataPath,ProtocolName,'Session Data'))
mkdir(fullfile(DataPath,ProtocolName,'Session Settings'))

% Ensure that a default settings file exists
DefaultSettingsFilePath = fullfile(DataPath,ProtocolName,'Session Settings', 'DefaultSettings.mat');
if ~exist(DefaultSettingsFilePath)
    ProtocolSettings = struct;
    save(DefaultSettingsFilePath, 'ProtocolSettings')
end
UpdateDataFile(ProtocolName, BpodSystem.GUIData.DummySubjectString);
BpodSystem.GUIData.ProtocolSelectorLastValue = 1;

%% ProtocolSelector
% Make sure a default settings file exists
SettingsFolder = fullfile(BpodSystem.Path.DataFolder,BpodSystem.GUIData.DummySubjectString,ProtocolName, 'Session Settings');
if ~exist(SettingsFolder)
    mkdir(SettingsFolder);
end
DefaultSettingsPath = fullfile(SettingsFolder,'DefaultSettings.mat');
% Ensure that a default settings file exists
if ~exist(DefaultSettingsPath)
    ProtocolSettings = struct;
    save(DefaultSettingsPath, 'ProtocolSettings')
end
    
UpdateDataFile(ProtocolName, BpodSystem.GUIData.DummySubjectString);
BpodSystem.Status.CurrentProtocolName = ProtocolName;

%% SubjectSelector
SelectedName = AnimalID;
SettingsPath = fullfile(BpodSystem.Path.DataFolder,SelectedName,ProtocolName,'Session Settings');
Candidates = dir(SettingsPath);
nSettingsFiles = 0;
SettingsFileNames = cell(1);
for x = 3:length(Candidates)
    Extension = Candidates(x).name;
    Extension = Extension(length(Extension)-2:length(Extension));
    if strcmp(Extension, 'mat')
        nSettingsFiles = nSettingsFiles + 1;
        Name = Candidates(x).name;
        SettingsFileNames{nSettingsFiles} = Name(1:end-4);
    end
end
UpdateDataFile(ProtocolName, SelectedName);

LaunchProtocol(AnimalID, TheProtocol, DefaultSettingsFilePath);

function UpdateDataFile(ProtocolName, SubjectName)
global BpodSystem
DateInfo = datestr(now, 30); 
DateInfo(DateInfo == 'T') = '_';
LocalDir = BpodSystem.Path.DataFolder(max(find(BpodSystem.Path.DataFolder(1:end-1) == filesep)+1):end);
FileName = [SubjectName '_' ProtocolName '_' DateInfo '.mat'];
BpodSystem.Path.CurrentDataFile = fullfile(BpodSystem.Path.DataFolder, SubjectName, ProtocolName, 'Session Data', FileName);

function LaunchProtocol(AnimalID, TheProtocol, DefaultSettingsFilePath)
global BpodSystem

ProtocolName = TheProtocol;

SubjectName = AnimalID;

SettingsFileName = DefaultSettingsFilePath;

ProtocolFileName = fullfile(BpodSystem.Path.ProtocolFolder, ProtocolName, [ProtocolName '.m']);
DataFolder = fullfile(BpodSystem.Path.DataFolder,SubjectName,ProtocolName,'Session Data');

if ~exist(DataFolder)
    mkdir(DataFolder);
end
BpodSystem.Status.Live = 1;
BpodSystem.GUIData.ProtocolName = ProtocolName;
BpodSystem.GUIData.SubjectName = SubjectName;
BpodSystem.GUIData.SettingsFileName = SettingsFileName;
BpodSystem.Path.Settings = SettingsFileName;
SettingStruct = load(BpodSystem.Path.Settings);
F = fieldnames(SettingStruct);
FieldName = F{1};
BpodSystem.ProtocolSettings = eval(['SettingStruct.' FieldName]);
BpodSystem.Data = struct;
ProtocolPath = fullfile(BpodSystem.Path.ProtocolFolder,ProtocolName,[ProtocolName '.m']);
addpath(ProtocolPath);
set(BpodSystem.GUIHandles.RunButton, 'cdata', BpodSystem.GUIData.PauseButton, 'TooltipString', 'Press to pause session');
BpodSystem.Status.BeingUsed = 1;
BpodSystem.ProtocolStartTime = now*100000;
run(ProtocolPath);

function OutputString = Spaces2Underscores(InputString)
SpaceIndexes = InputString == ' ';
InputString(SpaceIndexes) = '_';
OutputString = InputString;