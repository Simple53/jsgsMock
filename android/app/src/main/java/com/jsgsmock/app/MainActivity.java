package com.jsgsmock.app;

import android.annotation.SuppressLint;
import android.app.PictureInPictureParams;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
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
import androidx.webkit.WebViewAssetLoader;

public class MainActivity extends AppCompatActivity {

    private WebView mWebView;
    private ValueCallback<Uri[]> mUploadCallback;
    private static final int FILE_CHOOSER_REQUEST_CODE = 1001;
    private long mLastBackPressTime = 0;

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

    @Override
    public void onPictureInPictureModeChanged(boolean isInPictureInPictureMode, Configuration newConfig) {
        super.onPictureInPictureModeChanged(isInPictureInPictureMode, newConfig);
        if (mWebView != null) {
            mWebView.evaluateJavascript("if (typeof onAndroidPipModeChanged === 'function') onAndroidPipModeChanged(" + isInPictureInPictureMode + ");", null);
        }
    }
}
