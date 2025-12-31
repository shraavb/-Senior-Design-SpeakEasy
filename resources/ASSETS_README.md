# App Assets for Mobile Deployment

Place the following image files in this directory to generate app icons and splash screens:

## Required Files

### 1. App Icon
- **Filename:** `icon.png`
- **Size:** 1024x1024 pixels
- **Format:** PNG (no transparency for iOS)
- **Content:** Your SpeakEasy logo centered

### 2. Splash Screen
- **Filename:** `splash.png`
- **Size:** 2732x2732 pixels
- **Format:** PNG
- **Content:** Logo centered on background color

### 3. Android Adaptive Icons (Optional but Recommended)
- **Foreground:** `icon-foreground.png` (1024x1024, transparent background)
- **Background:** `icon-background.png` (1024x1024, solid color or pattern)

## Generating All Sizes

Once you have the source images, run:

```bash
npx capacitor-assets generate
```

This will automatically create all required sizes for:
- iOS App Icons (various sizes from 20x20 to 1024x1024)
- Android Icons (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi)
- Splash screens for all device sizes

## Design Tips

1. **Keep it simple** - Icons should be recognizable at small sizes
2. **Use bold colors** - Stand out on both light and dark home screens
3. **Avoid text** - Text becomes unreadable at small icon sizes
4. **Center your logo** - Leave padding around edges (safe zone)
5. **Test on devices** - Preview how icons look on actual devices

## After Generating

The assets will be placed in:
- `ios/App/App/Assets.xcassets/`
- `android/app/src/main/res/`

Then sync the changes:
```bash
npx cap sync
```
