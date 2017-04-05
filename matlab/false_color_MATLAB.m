clear all
clc

bkg_eosin=1000;
bkg_draq5=350;
k_eosin=0.011;
k_draq5=0.038;
voff1=10;
hoff1=-50;

draq5=imread(['C:\Users\AERB\Desktop\draq5.tif']);
eosin=imread(['C:\Users\AERB\Desktop\nhs.tif']);

eosin=eosin-bkg_eosin;
draq5=draq5-bkg_draq5;

draq5=double(draq5);
eosin=double(eosin);


eosin=eosin.^(0.75);
draq5=draq5.^(1);


% % Vertical shifting
if size(draq5,1)>size(eosin,1)
    if voff1>0
        draq5=draq5(1:size(eosin,1),:);
        eosin=eosin(1:end-voff1,:);
        draq5=draq5(voff1+1:end,:);
    else
        draq5=draq5(1:size(eosin,1),:);
        draq5=draq5(1:end+voff1,:);
        eosin=eosin(-voff1+1:end,:);
    end
else
    if voff1>0
        eosin=eosin(1:size(draq5,1),:);
        eosin=eosin(1:end-voff1,:);
        draq5=draq5(voff1+1:end,:);
    else
        eosin=eosin(1:size(draq5,1),:);
        draq5=draq5(1:end+voff1,:);
        eosin=eosin(-voff1+1:end,:);
    end
end
% 
% % Horizontal shifting
if size(draq5,2)>size(eosin,2)
    if hoff1>0
        draq5=draq5(:,1:size(eosin,2));
        draq5=draq5(:,hoff1:end);
        eosin=eosin(:,1:end-(hoff1-1));
    else
        draq5=draq5(:,1:size(eosin,2));
        eosin=eosin(:,-hoff1:end);
        draq5=draq5(:,1:end-(-hoff1-1));
    end
else
    if hoff1>0
        eosin=eosin(:,1:size(draq5,2));
        eosin=eosin(:,hoff1:end);
        draq5=draq5(:,1:end-(hoff1-1));
    else
        eosin=eosin(:,1:size(draq5,2));
        draq5=draq5(:,-hoff1:end);
        eosin=eosin(:,1:end-(-hoff1-1));
    end
end

ind=find(eosin>50);
m1=mean(eosin(ind))*8;
eosin=eosin*(65535/m1)*(255/65535);
ind=find(draq5>500);
m2=mean(draq5(ind))*8;
draq5=draq5*(65535/m2)*(255/65535);

beta1=0.860;
beta2=0.05;
beta3=1;

beta4=1;
beta5=0.300;
beta6=0.544;

eosin(find(eosin<0))=0;
draq5(find(draq5<0))=0;


R=exp(-beta2*eosin*k_eosin).*exp(-beta1*draq5*k_draq5);
G=exp(-beta4*eosin*k_eosin).*exp(-beta3*draq5*k_draq5);
B=exp(-beta6*eosin*k_eosin).*exp(-beta5*draq5*k_draq5);

im(:,:,1)=uint8(R*255);
im(:,:,2)=uint8(G*255);
im(:,:,3)=uint8(B*255);

imwrite(im,'draq5eo_he.tif');
