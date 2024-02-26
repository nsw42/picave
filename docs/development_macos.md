# Setting up your development environment on macOS

## Install dependencies

```bash
brew install gtk4
brew install mpg123
brew install mpv
brew install yt-dlp
```

## Install go compiler

```bash
brew install go
```

(Alternatively,
`asdf plugin add golang; asdf install golang latest; asdf local golang latest`,
if you're set up with [asdf](https://github.com/asdf-vm/asdf))

## Cross-building from macOS to Raspberry Pi

The `build.sh` script relies upon the cross-builder Docker images at
<https://github.com/nsw42/go-gtk4-cross-compile>.
