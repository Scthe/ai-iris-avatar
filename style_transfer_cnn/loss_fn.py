import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

# https://pytorch.org/vision/stable/models/generated/torchvision.models.vgg19.html#torchvision.models.vgg19
VGG_OUTPUT_LAYERS = {"vgg16": [1, 11, 18, 25, 20], "vgg19": [1, 6, 11, 20, 29, 22]}


class VGGPerceptualLoss(nn.Module):
    """
    If you use MSE on RGB data you get coonservative 'something in the middle'
    brown filter. That's cause red+blue+yellow (the 'natural' world primaries)
    create brown when mixed. So the brown color is a safe color that
    will give best average loss regardless of the input and output (!).
    Fun thing, you can overfit or try to power through it and get better
    results. For obvious reasons you do not want to do that.

    To solve this just use perceptual loss. The most basic would
    be MSE of CIE Lab color space [1]. Turns out that neural nets
    get good results here too. As in similar to the human perception.
    Using VGG19 (VGG16 is also popular here).

    For style transfer in particular, Gram matrices are constructed
    to extract the features [3]. In particular, which features
    tend to activate together. This creates the style loss function.

    Normally in style transfer you would also add content loss function.
    But, since we used SD to generate target images...


    # References:

    [1] Zhang R., Isola P., Efros A.: Colorful Image Colorization, page 4.
        See also R. Zhang's presentation: https://www.youtube.com/watch?v=0xmVraAvAAc
    [2] https://www.youtube.com/watch?v=nbRkLE2fiVI
    [3] https://www.youtube.com/watch?v=AJOyMJjPDtE
    """

    def __init__(self, device):
        super(VGGPerceptualLoss, self).__init__()

        # vgg_network, output_features = self._get_layers(device)
        vgg_network = models.vgg19(weights="DEFAULT").to(device)
        vgg_features = vgg_network.features.to(device)
        # print(vgg_network)

        max_feature = VGG_OUTPUT_LAYERS["vgg19"][-1] + 1
        vgg_used_layers = list(vgg_features.children())[:max_feature]
        self.vgg = nn.Sequential(*vgg_used_layers).to(device).eval()
        self.vgg = self.vgg.requires_grad_(False)
        for p in self.vgg.parameters():  # ...
            p.requires_grad = False
        # print(self.vgg)

        """
        vgg_mean = (0.485, 0.456, 0.406)
        vgg_std = (0.229 * rgb_range, 0.224 * rgb_range, 0.225 * rgb_range)
        self.sub_mean = common.MeanShift(rgb_range, vgg_mean, vgg_std)
        """

    """
    def _get_layers(self, device):
        vgg_network = models.vgg19(pretrained=True).to(device)
        vgg_features = vgg_network.features.to(device).eval()
        for p in vgg_features.parameters():
            p.requires_grad = False
        output_layers = [
            1,
            6,
            11,
            20,
            29,
            22,
        ]  # feature maps. Marks the end of consecutive (convolution+activation)
        return vgg_network, [vgg_features[i] for i in output_layers]
    """

    def forward(self, input: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        def _forward(x):
            # x = self.sub_mean(x)
            x = self.vgg(x)
            return x

        # print("input", input.shape)
        # print("target", target.shape)
        vgg_input = _forward(input[0])
        with torch.no_grad():
            vgg_target = _forward(target[0].detach())

        loss = F.mse_loss(vgg_input, vgg_target)

        return loss
