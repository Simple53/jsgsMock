package com.jsgsmock.app;

import android.annotation.SuppressLint;
import android.app.PictureInPictureParams;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.util.Rational;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.FileProvider;
import androidx.webkit.WebViewAssetLoader;

import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.atomic.AtomicBoolean;

public class MainActivity extends AppCompatActivity {

    private WebView mWebView;
    private ValueCallback<Uri[]> mUploadCallback;
    private static final int FILE_CHOOSER_REQUEST_CODE = 1001;
    private static final int INSTALL_PERM_REQUEST_CODE = 1002;
    private long mLastBackPressTime = 0;
    private final AtomicBoolean mIsDownloadingApk = new AtomicBoolean(false);
    private File mPendingInstallApkFile = null;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        mWebView = new WebView(this);
        setContentView(mWebView);

        WebSettings settings = mWebView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);

        // 注入 Android 原生 JS 桥接对象，支持版本获取、下载更新、屏幕旋转锁定解除与原生画中画
        mWebView.addJavascriptInterface(new Object() {
            @android.webkit.JavascriptInterface
            public String getAppVersion() {
                try {
                    return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
                } catch (Exception e) {
                    return "1.4.6";
                }
            }

            @android.webkit.JavascriptInterface
            public void openDownloadUrl(String url) {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception e) {
                    runOnUiThread(() -> Toast.makeText(MainActivity.this, "启动下载失败: " + e.getMessage(), Toast.LENGTH_SHORT).show());
                }
            }

            /**
             * 标识原生壳支持 App 内一键联网下载与自动安装 APK
             */
            @android.webkit.JavascriptInterface
            public boolean supportsInAppUpdate() {
                return true;
            }

            /**
             * 在 App 内部后台下载最新 APK 并自动调起系统安装器（通过 onApkDownloadProgress 回传进度）
             */
            @android.webkit.JavascriptInterface
            public void downloadAndInstallApk(String urlStr, String version) {
                if (urlStr == null || urlStr.trim().isEmpty()) {
                    notifyUpdateProgress(-1, "下载地址为空");
                    return;
                }
                if (!mIsDownloadingApk.compareAndSet(false, true)) {
                    runOnUiThread(() -> Toast.makeText(MainActivity.this, "正在下载更新包，请稍候...", Toast.LENGTH_SHORT).show());
                    return;
                }
                final String safeVer = (version == null || version.trim().isEmpty())
                        ? "latest"
                        : version.trim().replaceAll("[^a-zA-Z0-9._-]", "");
                new Thread(() -> {
                    HttpURLConnection conn = null;
                    File tmpFile = null;
                    try {
                        notifyUpdateProgress(0, "正在连接更新服务器...");
                        String currentUrl = urlStr.trim();
                        int redirects = 0;
                        while (redirects < 6) {
                            URL u = new URL(currentUrl);
                            conn = (HttpURLConnection) u.openConnection();
                            conn.setInstanceFollowRedirects(false);
                            conn.setConnectTimeout(15000);
                            conn.setReadTimeout(30000);
                            conn.setRequestProperty("User-Agent", "jsgsMock-Android-Updater");
                            int code = conn.getResponseCode();
                            if (code == HttpURLConnection.HTTP_MOVED_PERM
                                    || code == HttpURLConnection.HTTP_MOVED_TEMP
                                    || code == HttpURLConnection.HTTP_SEE_OTHER
                                    || code == 307 || code == 308) {
                                String loc = conn.getHeaderField("Location");
                                conn.disconnect();
                                if (loc == null || loc.isEmpty()) {
                                    throw new Exception("重定向地址为空 (HTTP " + code + ")");
                                }
                                currentUrl = new URL(u, loc).toString();
                                redirects++;
                                continue;
                            }
                            if (code < 200 || code >= 300) {
                                conn.disconnect();
                                throw new Exception("服务器返回异常状态码 HTTP " + code);
                            }
                            break;
                        }
                        if (redirects >= 6 || conn == null) {
                            throw new Exception("下载链接重定向次数过多或无法建立连接");
                        }

                        long totalBytes = conn.getContentLengthLong();
                        File baseDir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                        if (baseDir == null) {
                            baseDir = getCacheDir();
                        }
                        if (!baseDir.exists()) {
                            baseDir.mkdirs();
                        }
                        File outFile = new File(baseDir, "jsgsMock-v" + safeVer + ".apk");
                        tmpFile = new File(baseDir, "jsgsMock-v" + safeVer + ".apk.tmp");
                        if (tmpFile.exists()) {
                            tmpFile.delete();
                        }

                        try (InputStream in = new BufferedInputStream(conn.getInputStream());
                             FileOutputStream out = new FileOutputStream(tmpFile)) {
                            byte[] buf = new byte[16384];
                            long downloaded = 0;
                            int lastPercent = -1;
                            int n;
                            while ((n = in.read(buf)) != -1) {
                                out.write(buf, 0, n);
                                downloaded += n;
                                if (totalBytes > 0) {
                                    int pct = (int) Math.min(99, (downloaded * 100L) / totalBytes);
                                    if (pct != lastPercent) {
                                        lastPercent = pct;
                                        double mbDone = downloaded / (1024.0 * 1024.0);
                                        double mbTotal = totalBytes / (1024.0 * 1024.0);
                                        notifyUpdateProgress(pct, String.format("正在下载安装包... %d%% (%.1f / %.1f MB)", pct, mbDone, mbTotal));
                                    }
                                } else {
                                    if (downloaded % (256 * 1024) < 16384) {
                                        double mbDone = downloaded / (1024.0 * 1024.0);
                                        notifyUpdateProgress(50, String.format("正在下载安装包... 已下载 %.1f MB", mbDone));
                                    }
                                }
                            }
                            out.flush();
                        } finally {
                            conn.disconnect();
                        }

                        if (!tmpFile.exists() || tmpFile.length() < 102400) {
                            throw new Exception("下载文件不完整，请尝试切换通道重试");
                        }
                        if (outFile.exists()) {
                            outFile.delete();
                        }
                        if (!tmpFile.renameTo(outFile)) {
                            throw new Exception("保存安装包失败");
                        }

                        notifyUpdateProgress(100, "下载完成，正在调起安装程序...");
                        final File readyApk = outFile;
                        runOnUiThread(() -> installApkFile(readyApk));
                    } catch (Exception e) {
                        if (tmpFile != null && tmpFile.exists()) {
                            tmpFile.delete();
                        }
                        String msg = e.getMessage() != null ? e.getMessage() : "网络连接失败";
                        notifyUpdateProgress(-1, "下载失败: " + msg);
                    } finally {
                        mIsDownloadingApk.set(false);
                    }
                }).start();
            }

            /**
             * 强制设置屏幕方向，绕过系统的旋转锁定限制
             * @param orientation "landscape" (强制横屏，解开系统竖屏锁定), "portrait" (强制竖屏), "unspecified" (恢复系统自由判断)
             */
            @android.webkit.JavascriptInterface
            public void setScreenOrientation(String orientation) {
                runOnUiThread(() -> {
                    try {
                        if ("landscape".equalsIgnoreCase(orientation)) {
                            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
                        } else if ("portrait".equalsIgnoreCase(orientation)) {
                            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
                        } else {
                            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
                        }
                    } catch (Exception ex) {
                        ex.printStackTrace();
                    }
                });
            }

            /**
             * 调用 Android 原生系统级画中画 (Picture-in-Picture)
             */
            @android.webkit.JavascriptInterface
            public void enterPip() {
                runOnUiThread(() -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        try {
                            PictureInPictureParams.Builder builder = new PictureInPictureParams.Builder();
                            Rational aspectRatio = new Rational(16, 9);
                            builder.setAspectRatio(aspectRatio);
                            enterPictureInPictureMode(builder.build());
                        } catch (Exception e) {
                            try {
                                enterPictureInPictureMode();
                            } catch (Exception ex) {
                                Toast.makeText(MainActivity.this, "进入画中画失败: " + ex.getMessage(), Toast.LENGTH_SHORT).show();
                            }
                        }
                    } else {
                        Toast.makeText(MainActivity.this, "当前系统版本低于 Android 8.0，不支持系统画中画", Toast.LENGTH_SHORT).show();
                    }
                });
            }
        }, "AndroidApp");

        // 使用 AndroidX 官方推荐的 WebViewAssetLoader 将本地 Assets 映射为合法的虚拟安全域
        // 彻底根治本地 file:/// 协议下 Fetch/XHR/CORS 无法读取 JSON 题库的问题
        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        mWebView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (url.startsWith("https://appassets.androidplatform.net/") || url.startsWith("file:///")) {
                    return false;
                }
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                        startActivity(intent);
                        return true;
                    } catch (Exception e) {
                        return true;
                    }
                }
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    startActivity(intent);
                    return true;
                } catch (Exception e) {
                    return true;
                }
            }
        });

        mWebView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (mUploadCallback != null) {
                    mUploadCallback.onReceiveValue(null);
                }
                mUploadCallback = filePathCallback;

                Intent intent = fileChooserParams.createIntent();
                try {
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST_CODE);
                } catch (Exception e) {
                    mUploadCallback = null;
                    return false;
                }
                return true;
            }
        });

        mWebView.loadUrl("https://appassets.androidplatform.net/assets/web/index.html");

        // 双击返回键退出
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (mWebView.canGoBack()) {
                    mWebView.goBack();
                } else {
                    long now = System.currentTimeMillis();
                    if (now - mLastBackPressTime < 2000) {
                        finish();
                    } else {
                        mLastBackPressTime = now;
                        Toast.makeText(MainActivity.this, "再按一次退出 jsgsMock", Toast.LENGTH_SHORT).show();
                    }
                }
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == INSTALL_PERM_REQUEST_CODE) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && getPackageManager().canRequestPackageInstalls()) {
                if (mPendingInstallApkFile != null && mPendingInstallApkFile.exists()) {
                    File pending = mPendingInstallApkFile;
                    mPendingInstallApkFile = null;
                    installApkFile(pending);
                }
            } else {
                notifyUpdateProgress(-1, "未授予安装未知应用权限，请在系统设置中允许后重新点击更新");
            }
            return;
        }
        if (requestCode == FILE_CHOOSER_REQUEST_CODE) {
            if (mUploadCallback == null) return;
            Uri[] results = null;
            if (resultCode == RESULT_OK && data != null) {
                if (data.getData() != null) {
                    results = new Uri[]{data.getData()};
                } else if (data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    results = new Uri[count];
                    for (int i = 0; i < count; i++) {
                        results[i] = data.getClipData().getItemAt(i).getUri();
                    }
                }
            }
            mUploadCallback.onReceiveValue(results);
            mUploadCallback = null;
        }
    }

    private void notifyUpdateProgress(int percent, String status) {
        runOnUiThread(() -> {
            if (mWebView != null) {
                String safeMsg = JSONObject.quote(status != null ? status : "");
                mWebView.evaluateJavascript("if (typeof window.onApkDownloadProgress === 'function') window.onApkDownloadProgress(" + percent + ", " + safeMsg + ");", null);
            }
        });
    }

    private void installApkFile(File apkFile) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !getPackageManager().canRequestPackageInstalls()) {
                mPendingInstallApkFile = apkFile;
                Toast.makeText(this, "请先允许 jsgsMock 安装未知来源应用，授权后将自动安装", Toast.LENGTH_LONG).show();
                Intent permIntent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName()));
                startActivityForResult(permIntent, INSTALL_PERM_REQUEST_CODE);
                return;
            }
            Uri apkUri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", apkFile);
            Intent installIntent = new Intent(Intent.ACTION_VIEW);
            installIntent.setDataAndType(apkUri, "application/vnd.android.package-archive");
            installIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(installIntent);
        } catch (Exception e) {
            notifyUpdateProgress(-1, "调起系统安装器失败: " + e.getMessage());
            Toast.makeText(this, "调起安装器失败: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    @Override
    public void onPictureInPictureModeChanged(boolean isInPictureInPictureMode, Configuration newConfig) {
        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig);
        if (mWebView != null) {
            mWebView.evaluateJavascript("if (typeof onAndroidPipModeChanged === 'function') onAndroidPipModeChanged(" + isInPictureInPictureMode + ");", null);
        }
    }
}
