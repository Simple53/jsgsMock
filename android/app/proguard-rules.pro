# 保持 WebView JavascriptInterface 注解和方法，防止混淆被 strip
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# 保持核心包类结构
-keep class com.jsgsmock.app.** { *; }
