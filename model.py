import torch
import torch.nn as nn


class _netG(nn.Module):
    def __init__(self, opt):
        super(_netG, self).__init__()
        self.multiplierG = opt.imageSize / (opt.patchSize * 2)
        self.ngpu = opt.ngpu
        
        main = nn.Sequential()
        
        # Conv
        
        main.add_module(
            'ENC_imsize.{0}-{1}_depth.{2}-{3}.conv2d'.format(opt.imageSize, opt.imageSize // 2, opt.nc, opt.ndf),
            nn.Conv2d(opt.nc, opt.ndf, 4, 2, 1, bias=False))
        main.add_module('ENC_imsize.{0}_depth.{1}.lrelu'.format(opt.imageSize // 2, opt.ndf),
                        nn.LeakyReLU(0.2, inplace=True))
        csize, cndf = int(opt.imageSize / 2), opt.ndf
        
        while csize > 4:
            in_feat = cndf
            out_feat = cndf * 2
            main.add_module('ENC_imsize.{0}-{1}_depth.{2}-{3}.conv2d'.format(csize, csize // 2, in_feat, out_feat),
                            nn.Conv2d(in_feat, out_feat, 4, 2, 1, bias=False))
            main.add_module('ENC_imsize.{0}_depth.{1}.batchnorm'.format(csize // 2, out_feat),
                            nn.BatchNorm2d(out_feat))
            main.add_module('ENC_imsize.{0}_depth.{1}.lrelu'.format(csize // 2, out_feat),
                            nn.LeakyReLU(0.2, inplace=True))
            cndf = cndf * 2
            csize = csize // 2
        
        bottleneck = cndf * 2
        csize = int(csize)
        
        main.add_module('ENC_imsize.{0}-{1}_depth.{2}-{3}.conv2d'.format(csize, 1, cndf, bottleneck),
                        nn.Conv2d(cndf, bottleneck, 4, 1, 0, bias=False))
        main.add_module('ENC_imsize.{0}_depth.{1}.batchnorm'.format(1, bottleneck),
                        nn.BatchNorm2d(bottleneck))
        main.add_module('ENC_imsize.{0}_depth.{1}.lrelu'.format(1, bottleneck),
                        nn.LeakyReLU(0.2, inplace=True))

        # Deconv
        
        ngf = opt.imageSize / opt.patchSize * opt.nef / 2
        cngf, tisize = ngf // 2, 4
        while tisize != opt.imageSize:
            cngf = cngf * 2
            tisize = tisize * 2
        
        cngf = int(cngf)
        tisize = int(tisize)
        csize = 4
        
        main.add_module('DEC_imsize.{0}-{1}_depth.{2}-{3}.deconv2d'.format(1, csize, bottleneck, cngf),
                        nn.ConvTranspose2d(bottleneck, cngf, 4, 1, 0, bias=False))
        main.add_module('DEC_imsize.{0}_depth.{1}.batchnorm'.format(csize, cngf), nn.BatchNorm2d(cngf))
        main.add_module('DEC_imsize.{0}_depth.{1}.relu'.format(csize, cngf), nn.ReLU(True))
        
        while csize < opt.patchSize // 2:
            main.add_module('DEC_imsize.{0}-{1}_depth.{2}-{3}.deconv2d'.format(csize, csize * 2, cngf, cngf // 2),
                            nn.ConvTranspose2d(cngf, cngf // 2, 4, 2, 1, bias=False))
            main.add_module('DEC_imsize.{0}_depth.{1}.batchnorm'.format(csize * 2, cngf // 2),
                            nn.BatchNorm2d(cngf // 2))
            main.add_module('DEC_imsize.{0}_depth.{1}.relu'.format(csize * 2, cngf // 2),
                            nn.ReLU(True))
            
            cngf = cngf // 2
            csize = csize * 2
        
        main.add_module('DEC_imsize.{0}-{1}_depth.{2}-{3}.deconv2d'.format(csize, csize * 2, cngf, opt.nc),
                        nn.ConvTranspose2d(cngf, opt.nc, 4, 2, 1, bias=False))
        main.add_module('DEC_imsize.{0}_depth.{1}.final_tanh'.format(csize * 2, opt.nc),
                        nn.Tanh())
        
        self.main = main
        
        
        # # input is (nc) x 128 x 128
        # nn.Conv2d(opt.nc, opt.nef, 4, 2, 1, bias=False), #modified
        # nn.LeakyReLU(0.2, inplace=True),
        # # state size: (nef) x 64 x 64
        # nn.Conv2d(opt.nef, opt.nef, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef),
        # nn.LeakyReLU(0.2, inplace=True),
        # # state size: (nef) x 32 x 32
        # nn.Conv2d(opt.nef, opt.nef * 2, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 2),
        # nn.LeakyReLU(0.2, inplace=True),
        # # state size: (nef*2) x 16 x 16
        # nn.Conv2d(opt.nef * 2, opt.nef * 4, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 4),
        # nn.LeakyReLU(0.2, inplace=True),
        # # state size: (nef*4) x 8 x 8
        # nn.Conv2d(opt.nef * 4, opt.nef * 8, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 8),
        # nn.LeakyReLU(0.2, inplace=True),
        # # state size: (nef*8) x 4 x 4
        # nn.Conv2d(opt.nef * 8, opt.nef * 16, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 16),
        # nn.LeakyReLU(0.2, inplace=True),
        # # state size: (nef*16) x 2 x 2
        # nn.Conv2d(opt.nef * 16, opt.nef * 32, 4, 2, 1, bias=False),
        # # state size: (nef*32) x 1 x 1
        # nn.BatchNorm2d(opt.nef * 32),
        # nn.LeakyReLU(0.2, inplace=True),
        # # input is nef * 32, going into a convolution
        # nn.ConvTranspose2d(opt.nef * 32, opt.nef * 16, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 16),
        # nn.ReLU(True),
        # # state size. (ngf*16) x 2 x 2
        # nn.ConvTranspose2d(opt.nef * 16, opt.nef * 8, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 8),
        # nn.ReLU(True),
        # # state size. (ngf*8) x 4 x 4
        # nn.ConvTranspose2d(opt.nef * 8, opt.nef * 4, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 4),
        # nn.ReLU(True),
        # # state size. (ngf*4) x 8 x 8
        # nn.ConvTranspose2d(opt.nef * 4, opt.nef * 2, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef * 2),
        # nn.ReLU(True),
        # # state size. (ngf*2) x 16 x 16
        # nn.ConvTranspose2d(opt.nef * 2, opt.nef, 4, 2, 1, bias=False),
        # nn.BatchNorm2d(opt.nef),
        # nn.ReLU(True),
        # # state size. (ngf) x 32 x 32
        # nn.ConvTranspose2d(opt.nef, opt.nc, 4, 2, 1, bias=False),
        # nn.Tanh()
        # # state size. (nc) x 64 x 64
    
    def forward(self, input):
        if isinstance(input.data, torch.cuda.FloatTensor) and self.ngpu > 1:
            output = nn.parallel.data_parallel(self.main, input, range(self.ngpu))
        else:
            output = self.main(input)
        return output


class _netlocalD(nn.Module):
    def __init__(self, opt):
        super(_netlocalD, self).__init__()
        self.ngpu = opt.ngpu
        
        main = nn.Sequential()
        
        # Conv
        
        main.add_module(
            'DISC_imsize.{0}-{1}_depth.{2}-{3}.conv2d'.format(opt.patchSize, opt.patchSize // 2, opt.nc, opt.nef),
            nn.Conv2d(opt.nc, opt.nef, 4, 2, 1, bias=False))
        main.add_module('DISC_imsize.{0}_depth.{1}.lrelu'.format(opt.imageSize // 2, opt.nef),
                        nn.LeakyReLU(0.2, inplace=True))
        csize, cnef = int(opt.patchSize / 2), opt.nef
        
        while csize > 4:
            in_feat = cnef
            out_feat = cnef * 2
            main.add_module('DISC_imsize.{0}-{1}_depth.{2}-{3}.conv2d'.format(csize, csize // 2, in_feat, out_feat),
                            nn.Conv2d(in_feat, out_feat, 4, 2, 1, bias=False))
            main.add_module('DISC_imsize.{0}_depth.{1}.batchnorm'.format(csize // 2, out_feat),
                            nn.BatchNorm2d(out_feat))
            main.add_module('DISC_imsize.{0}_depth.{1}.lrelu'.format(csize // 2, out_feat),
                            nn.LeakyReLU(0.2, inplace=True))
            cnef = cnef * 2
            csize = csize // 2
        
        csize = int(csize)
        
        main.add_module('DISC_imsize.{0}-{1}_depth.{2}-{3}.conv2d'.format(csize, 1, cnef, 1),
                        nn.Conv2d(cnef, 1, 4, 1, 0, bias=False))
        main.add_module('DISC_imsize.{0}_depth.{1}.final_sigmoid'.format(1, 1),
                        nn.Sigmoid())
        
        self.main = main
        
        # self.main = nn.Sequential(
        #     # input is (nc) x 64 x 64
        #     nn.Conv2d(opt.nc, opt.ndf, 4, 2, 1, bias=False),
        #     nn.LeakyReLU(0.2, inplace=True),
        #     # state size. (ndf) x 32 x 32
        #     nn.Conv2d(opt.ndf, opt.ndf * 2, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(opt.ndf * 2),
        #     nn.LeakyReLU(0.2, inplace=True),
        #     # state size. (ndf*2) x 16 x 16
        #     nn.Conv2d(opt.ndf * 2, opt.ndf * 4, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(opt.ndf * 4),
        #     nn.LeakyReLU(0.2, inplace=True),
        #     # state size. (ndf*4) x 8 x 8
        #     nn.Conv2d(opt.ndf * 4, opt.ndf * 8, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(opt.ndf * 8),
        #     nn.LeakyReLU(0.2, inplace=True),
        #     # state size. (ndf*8) x 4 x 4
        #     nn.Conv2d(opt.ndf * 8, 1, 4, 1, 0, bias=False),
        #     nn.Sigmoid()
        # )
    
    def forward(self, input):
        if isinstance(input.data, torch.cuda.FloatTensor) and self.ngpu > 1:
            output = nn.parallel.data_parallel(self.main, input, range(self.ngpu))
        else:
            output = self.main(input)
        
        return output.view(-1, 1)
