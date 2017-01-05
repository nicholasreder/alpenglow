%%                         INPUTS                                     %%
clear all
clc
% Absolute path to data (should always be on desktop)
path='C:\Users\AERB\Desktop\';
email='adamkglaser@gmail.com';

% Sample dependent variables
dname='bead_phantom_2';
idx=1:1:511;
overlap=35;
S_start=0;
S_end=1;
mosaic_idx=70;
hoff=10;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%                         MIJI BATCH FILE                            %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

start_time = datestr(now);

% Create processed data folder and enter in

recycle off;
diary off;

mkdir(['F:\processed_data\' dname]);
cd(['F:\processed_data\' dname]);

% Turn log file on
if exist('log.out','file')~=0
    delete('log.out');
end
diary log.out

    % Read raw data
    % Stripe filter and flip alternating stripes
    % Save as en-face images for mosaicing

    [N,V,H,S,C]=get_metadata(path,dname,S_start);
    
    V=idx(end)*2;
    
    % Start Java Robot
    robot=java.awt.Robot;

    % Start Miji
    Miji(false);

for i=S_start:S_end

    I=read_data_wview_random(i,V,C,H,N,path,dname,idx);
    
    %I(:,:,1:V/2)=I(:,:,1:V/2)-I(:,:,V/2+1:end)/20;

    cd(['F:\processed_data\' dname]);
    mkdir(['F:\processed_data\' dname '\draq5']);
    mkdir(['F:\processed_data\' dname '\eosin']);

    if rem(i,2)==0
        for j=1:size(I,3)/2
            imwrite(fliplr(I(1+hoff:end,:,j)),['F:\processed_data\' dname '\eosin\im_' num2str(i,'%06d') '_' num2str(idx(j),'%06d') '.tif']);
            imwrite(fliplr(I(1:end-hoff,:,j+V/2)),['F:\processed_data\' dname '\draq5\im_' num2str(i,'%06d') '_' num2str(idx(j),'%06d') '.tif']);
        end
        imwrite(fliplr(max(I(1+hoff:end,:,12:V/2),[],3)),['F:\processed_data\' dname '\eosin\im_' num2str(i,'%06d') '_max.tif']);
        imwrite(fliplr(max(I(1:end-hoff,:,V/2+12:end),[],3)),['F:\processed_data\' dname '\draq5\im_' num2str(i,'%06d') '_max.tif']);
    else
        for j=1:size(I,3)/2
            imwrite(I(1+hoff:end,:,j),['F:\processed_data\' dname '\eosin\im_' num2str(i,'%06d') '_' num2str(idx(j),'%06d') '.tif']);  
            imwrite(I(1:end-hoff,:,j+V/2),['F:\processed_data\' dname '\draq5\im_' num2str(i,'%06d') '_' num2str(idx(j),'%06d') '.tif']); 
        end
        imwrite(max(I(1+hoff:end,:,12:V/2),[],3),['F:\processed_data\' dname '\eosin\im_' num2str(i,'%06d') '_max.tif']);
        imwrite(max(I(1:end-hoff,:,V/2+12:end),[],3),['F:\processed_data\' dname '\draq5\im_' num2str(i,'%06d') '_max.tif']);
    end

    clear I
    pause(3.0);

end

% Register a single middle plane
MIJ.start;
pause(1.0);
MIJ.run('Grid/Collection stitching', ['type=[Grid: row-by-row] order=[Left & Down] grid_size_x=1 grid_size_y='  num2str(S_end-S_start+1) ' tile_overlap=' num2str(overlap) ' first_file_index_i=' num2str(S_start) ' directory=F:\\processed_data\\' dname '\\eosin file_names=im_{iiiiii}_' num2str(mosaic_idx,'%06d') '.tif output_textfile_name=TileConfiguration.txt fusion_method=[Linear Blending] regression_threshold=0.3 max/avg_displacement_threshold=2500 absolute_displacement_threshold=5000 compute_overlap ignore_z_stage computation_parameters=[Save computation time (but use more RAM)] image_output=[Write to disk] output_directory=F:\\processed_data\\' dname '\\eosin']);
pause(1.0);
if exist(['F:\processed_data\' dname '\eosin\test.tif'],'file')~=0
    delete(['F:\processed_data\' dname '\eosin\test.tif']);
end
movefile(['F:\processed_data\' dname '\eosin\img_t1_z1_c1'],['F:\processed_data\' dname '\eosin\test.tif']);
pause(1.0);
MIJ.closeAllWindows;
pause(1.0);
MIJ.exit;
pause(1.0);

cd(['F:\processed_data\' dname]);

% Register all planes
for i=1:length(idx)
    MIJ.start;
    pause(1.0);
    fclose('all');
    fid=fopen(['F:\processed_data\' dname '\eosin\TileConfiguration.registered.txt'],'r');
    if exist(['F:\processed_data\' dname '\eosin\TileConfiguration_' num2str(idx(i),'%06d') '.txt'],'file')
        delete(['F:\processed_data\' dname '\eosin\TileConfiguration_' num2str(idx(i),'%06d') '.txt']);
    end
    fout=fopen(['F:\processed_data\' dname '\eosin\TileConfiguration_' num2str(idx(i),'%06d') '.txt'],'w'); % Open registered file for reading
    while ~feof(fid)
        line=fgets(fid); %# read line by line
        bool=isempty((strfind(line,['_' num2str(mosaic_idx,'%06d') '.tif'])));
        if bool==0;
            line=strrep(line,['_' num2str(mosaic_idx,'%06d') '.tif'],['_' num2str(idx(i),'%06d') '.tif']);
            fprintf(fout,'%s',line);
        else
            fprintf(fout,'%s',line);
        end
    end
    fclose('all');
    pause(1.0);
    MIJ.run('Grid/Collection stitching', ['type=[Positions from file] order=[Defined by TileConfiguration] directory=F:\\processed_data\\' dname '\\eosin layout_file=TileConfiguration_' num2str(idx(i),'%06d') '.txt fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=0.0 absolute_displacement_threshold=0.0 computation_parameters=[Save computation time (but use more RAM)] image_output=[Write to disk] output_directory=F:\\processed_data\\' dname '\\eosin']);
    pause(1.0);
    movefile(['F:\processed_data\' dname '\eosin\img_t1_z1_c1'],['F:\processed_data\' dname '\eosin\mosaic_' num2str(idx(i),'%06d') '.tif']);
    pause(1.0);
    MIJ.closeAllWindows;
    pause(1.0);
    MIJ.exit;
    pause(1.0);
end

% Register all planes
for i=1:length(idx)
    MIJ.start;
    pause(1.0);
    fclose('all');
    fid=fopen(['F:\processed_data\' dname '\eosin\TileConfiguration.registered.txt'],'r');
    if exist(['F:\processed_data\' dname '\draq5\TileConfiguration_' num2str(idx(i),'%06d') '.txt'],'file')
        delete(['F:\processed_data\' dname '\draq5\TileConfiguration_' num2str(idx(i),'%06d') '.txt']);
    end
    fout=fopen(['F:\processed_data\' dname '\draq5\TileConfiguration_' num2str(idx(i),'%06d') '.txt'],'w'); % Open registered file for reading
    while ~feof(fid)
        line=fgets(fid); %# read line by line
        bool=isempty((strfind(line,['_' num2str(mosaic_idx,'%06d') '.tif'])));
        if bool==0;
            line=strrep(line,['_' num2str(mosaic_idx,'%06d') '.tif'],['_' num2str(idx(i),'%06d') '.tif']);
            fprintf(fout,'%s',line);
        else
            fprintf(fout,'%s',line);
        end
    end
    fclose('all');
    pause(1.0);
    MIJ.run('Grid/Collection stitching', ['type=[Positions from file] order=[Defined by TileConfiguration] directory=F:\\processed_data\\' dname '\\draq5 layout_file=TileConfiguration_' num2str(idx(i),'%06d') '.txt fusion_method=[Linear Blending] regression_threshold=0.30 max/avg_displacement_threshold=0.0 absolute_displacement_threshold=0.0 computation_parameters=[Save computation time (but use more RAM)] image_output=[Write to disk] output_directory=F:\\processed_data\\' dname '\\draq5']);
    pause(1.0);
    movefile(['F:\processed_data\' dname '\draq5\img_t1_z1_c1'],['F:\processed_data\' dname '\draq5\mosaic_' num2str(idx(i),'%06d') '.tif']);
    pause(1.0);
    MIJ.closeAllWindows;
    pause(1.0);
    MIJ.exit;
    pause(1.0);
end

finish_time = datestr(now);
diary off
e_mail(email,'gmail','adamkglaser','AZAZ!!@$',...
    dname,{['Started At: ', start_time],['Completed At: ',finish_time]},{'log.out'});
