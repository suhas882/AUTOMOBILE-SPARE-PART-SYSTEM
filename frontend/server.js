const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const nodemailer = require('nodemailer');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*', // Allow all origins for simplicity; restrict in production
    methods: ['GET', 'POST']
  }
});

app.use(cors());
app.use(express.json());

// Email configuration (replace with your Gmail credentials or use environment variables)
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: 'your-email@gmail.com', // Replace with your Gmail address
    pass: 'your-app-password'     // Replace with your Gmail App Password (not regular password)
  }
});

// In-memory order storage (replace with MongoDB/MySQL in production)
let orders = [];

// Function to send email
const sendEmail = async (to, subject, html) => {
  try {
    await transporter.sendMail({
      from: '"Maridadi Auto Parts" <your-email@gmail.com>', // Sender address
      to, // Recipient email
      subject, // Email subject
      html // Email body
    });
    console.log(`Email sent to ${to}: ${subject}`);
  } catch (error) {
    console.error('Error sending email:', error);
  }
};

// Load orders from frontend (for migration)
app.post('/api/orders/migrate', (req, res) => {
  orders = req.body.orders.map(order => ({
    ...order,
    status: order.status || (order.accepted ? 'Processing' : 'Placed')
  }));
  res.json({ message: 'Orders migrated successfully' });
});

// Get all orders
app.get('/api/orders', (req, res) => {
  res.json(orders);
});

// Create a new order
app.post('/api/orders', async (req, res) => {
  const newOrder = {
    id: Date.now(),
    ...req.body,
    read: false,
    status: 'Placed',
    deliveryMessage: ''
  };
  orders.push(newOrder);
  io.emit('orderUpdate', newOrder); // Broadcast new order

  // Send order confirmation email
  if (newOrder.userDetails && newOrder.userDetails.email) {
    const itemsList = newOrder.items
      .map(item => `<li>${item.name} (${item.vehicle}) - $${item.price}</li>`)
      .join('');
    const emailContent = `
      <h2>Order Confirmation</h2>
      <p>Thank you for your order, ${newOrder.userDetails.name}!</p>
      <p><strong>Order ID:</strong> ${newOrder.id}</p>
      <p><strong>Status:</strong> ${newOrder.status}</p>
      <p><strong>Placed on:</strong> ${newOrder.date}</p>
      <h3>Items:</h3>
      <ul>${itemsList}</ul>
      <h3>Your Details:</h3>
      <p>Name: ${newOrder.userDetails.name}</p>
      <p>Email: ${newOrder.userDetails.email}</p>
      <p>Phone: ${newOrder.userDetails.phone}</p>
      <p>Address: ${newOrder.userDetails.address}</p>
      <p>You will receive updates on your order status via email.</p>
    `;
    await sendEmail(
      newOrder.userDetails.email,
      `Order Confirmation - Order #${newOrder.id}`,
      emailContent
    );
  }

  res.json(newOrder);
});

// Update order status
app.put('/api/orders/:id', async (req, res) => {
  const { id } = req.params;
  const { status, read } = req.body;
  const orderIndex = orders.findIndex(order => order.id === parseInt(id));
  if (orderIndex === -1) {
    return res.status(404).json({ error: 'Order not found' });
  }
  orders[orderIndex] = {
    ...orders[orderIndex],
    status,
    read: read !== undefined ? read : orders[orderIndex].read,
    deliveryMessage: ['Shipped', 'Delivered'].includes(status)
      ? 'Deliverable within 2-3 days'
      : orders[orderIndex].deliveryMessage
  };
  io.emit('orderUpdate', orders[orderIndex]); // Broadcast update

  // Send status update email
  if (orders[orderIndex].userDetails && orders[orderIndex].userDetails.email) {
    const emailContent = `
      <h2>Order Status Update</h2>
      <p>Dear ${orders[orderIndex].userDetails.name},</p>
      <p>Your order status has been updated.</p>
      <p><strong>Order ID:</strong> ${orders[orderIndex].id}</p>
      <p><strong>New Status:</strong> ${orders[orderIndex].status}</p>
      ${orders[orderIndex].deliveryMessage ? `<p><strong>Delivery:</strong> ${orders[orderIndex].deliveryMessage}</p>` : ''}
      <p>Check your order details in the <a href="http://localhost:8080">Maridadi Auto Parts</a> portal.</p>
    `;
    await sendEmail(
      orders[orderIndex].userDetails.email,
      `Order Status Update - Order #${orders[orderIndex].id}`,
      emailContent
    );
  }

  res.json(orders[orderIndex]);
});

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
