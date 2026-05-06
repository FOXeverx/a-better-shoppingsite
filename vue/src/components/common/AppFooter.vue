<template>
  <footer class="app-footer">
    <div class="container footer-content">
      <div class="footer-section">
        <h4>关于我们</h4>
        <ul>
          <li><a href="#">公司介绍</a></li>
          <li><a href="#">联系方式</a></li>
          <li><a href="#">隐私政策</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h4>客户服务</h4>
        <ul>
          <li><a href="#">帮助中心</a></li>
          <li><a href="#">配送说明</a></li>
          <li><a href="#">退换货政策</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h4>关注我们</h4>
        <ul>
          <li><a href="#">微信公众号</a></li>
          <li><a href="#">微博</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h4>扫码关注</h4>
        <div class="qr-code">
          <div class="placeholder"></div>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="container">
        <p>&copy; 2024 电商平台. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.app-footer {
  background: #2c3e50;
  color: #fff;
  margin-top: 40px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  padding: 40px 0;
  gap: 40px;
}

.footer-section {
  h4 {
    font-size: 16px;
    margin-bottom: 16px;
    font-weight: 600;
  }
  
  ul {
    li {
      margin-bottom: 10px;
      
      a {
        color: #a0aec0;
        font-size: 14px;
        transition: color 0.3s;
        
        &:hover {
          color: #fff;
        }
      }
    }
  }
  
  .qr-code {
    .placeholder {
      width: 100px;
      height: 100px;
      background: #4a5568;
      border-radius: 4px;
    }
  }
}

.footer-bottom {
  background: #1a252f;
  padding: 16px 0;
  text-align: center;
  
  p {
    color: #718096;
    font-size: 14px;
  }
}

@media (max-width: 768px) {
  .footer-content {
    flex-wrap: wrap;
    gap: 30px;
  }
  
  .footer-section {
    min-width: 45%;
  }
}
</style>