# Build Instructions

## Tailwind CSS Build

This project uses Tailwind CSS compiled from source instead of the CDN.

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Build CSS:
```bash
npm run build:css
```

Or use the build script:
```bash
./build.sh
```

### Production (Render)

The build process is automated. Render will:
1. Install npm dependencies (`package.json`)
2. Run `npm run build:css` to generate `app/static/css/tailwind.css`
3. Deploy the application

### Manual Build

If you need to rebuild manually:
```bash
npm install
npm run build:css
```

The compiled CSS will be in `app/static/css/tailwind.css`.

