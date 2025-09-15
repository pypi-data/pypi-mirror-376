import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:shimmer/shimmer.dart';

class FletCacheCircleAvatarControl extends StatelessWidget with FletStoreMixin {
  final Control? parent;
  final Control control;
  final List<Control> children;
  final bool parentDisabled;
  final FletControlBackend backend;

  const FletCacheCircleAvatarControl(
      {super.key,
      this.parent,
      required this.control,
      required this.children,
      required this.parentDisabled,
      required this.backend});

  @override
  Widget build(BuildContext context) {
    debugPrint("CircleAvatar build: ${control.id}");
    bool disabled = control.isDisabled || parentDisabled;

    return withPageArgs((context, pageArgs) {
      var foregroundImageSrc = control.attrString("foregroundImageSrc");
      var backgroundImageSrc = control.attrString("backgroundImageSrc");
      var contentCtrls =
          children.where((c) => c.name == "content" && c.isVisible);

      ImageProvider<Object>? backgroundImage;
      if (backgroundImageSrc != null) {
        var assetSrc =
            getAssetSrc(backgroundImageSrc, pageArgs.pageUri!, pageArgs.assetsDir);
        if (assetSrc.isFile) {
          backgroundImage = AssetImage(assetSrc.path);
        } else {
          backgroundImage = CachedNetworkImageProvider(assetSrc.path);
        }
      }

      Widget? child;
      if (foregroundImageSrc != null) {
        var assetSrc =
            getAssetSrc(foregroundImageSrc, pageArgs.pageUri!, pageArgs.assetsDir);

        final radius = control.attrDouble("radius", 40)!;
        final size = radius * 2;

        if (assetSrc.isFile) {
          child = ClipOval(
            child: Image.asset(
              assetSrc.path,
              fit: BoxFit.cover,
              width: size,
              height: size,
            ),
          );
        } else {
          child = ClipOval(
            child: CachedNetworkImage(
              imageUrl: assetSrc.path,
              fit: BoxFit.cover,
              width: size,
              height: size,
              fadeInDuration: const Duration(milliseconds: 300),

              placeholder: (context, url) => Shimmer.fromColors(
                baseColor: Colors.grey.shade400,
                highlightColor: Colors.grey.shade200,
                child: Container(
                  width: size,
                  height: size,
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                  ),
                ),
              ),

              errorWidget: (context, url, error) {
                backend.triggerControlEvent(control.id, "image_error", "foreground");
                return Container(
                  color: Colors.grey.withOpacity(0.1),
                  child: const Icon(
                    Icons.error_outline,
                    color: Colors.grey,
                  ),
                );
              },
            ),
          );
        }
      } else if (contentCtrls.isNotEmpty) {
        child = createControl(control, contentCtrls.first.id, disabled);
      }

      var avatar = CircleAvatar(
          backgroundImage: backgroundImage,
          backgroundColor: control.attrColor("bgColor", context),
          foregroundColor: control.attrColor("color", context),
          radius: control.attrDouble("radius"),
          minRadius: control.attrDouble("minRadius"),
          maxRadius: control.attrDouble("maxRadius"),
          onBackgroundImageError: backgroundImage != null
              ? (object, trace) {
                  backend.triggerControlEvent(
                      control.id, "image_error", "background");
                }
              : null,
          child: child);

      return constrainedControl(context, avatar, parent, control);
    });
  }
}