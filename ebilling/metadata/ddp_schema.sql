CREATE TABLE dbo.DDP (
    account_number VARCHAR(50),
    doc_type VARCHAR(20),
    customer_control VARCHAR(10),   -- Key, Sub, Both
    delivery_mode VARCHAR(10),      -- email, print, ignore, NULL
    updated_at DATETIME DEFAULT GETDATE()
);

INSERT INTO dbo.DDP VALUES
('ACC0010001', 'invoice', 'Key', 'email'),
('ACC0010002', 'invoice', 'Sub', 'print'),
('ACC0010003', 'invoice', 'Both', 'email'),
('ACC0010004', 'invoice', 'Key', 'ignore'),
('ACC0010005', 'invoice', 'Sub', NULL),

('ACC0020001', 'invoice', 'Key', 'email'),
('ACC0020002', 'invoice', 'Sub', 'print'),
('ACC0020003', 'invoice', 'Both', 'email'),
('ACC0020004', 'invoice', 'Key', 'ignore'),
('ACC0020005', 'invoice', 'Sub', NULL);

