/**
 * Canvas-Based DXF Fixture Editor
 * ================================
 * 
 * Interactive canvas for moving fixtures in DXF files
 * Features:
 * - Visual rendering of blueprints and fixtures
 * - Drag-and-drop fixture movement
 * - Real-time coordinate tracking
 * - Zoom and pan controls
 * - Gemini AI integration
 */

class CanvasEditor {
    constructor(canvasId, sessionId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.sessionId = sessionId;
        
        // Data
        this.fixtures = [];
        this.blueprint = [];
        this.bounds = null;
        
        // Interaction state
        this.selectedFixture = null;
        this.selectedFixtures = [];  // For multi-select
        this.isDragging = false;
        this.dragStartPos = null;
        this.dragStartCanvasPos = null;
        this.mouseDownTime = 0;  // Track click vs drag
        
        // View transform
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.minScale = 0.1;
        this.maxScale = 5;
        
        // Color palette for different fixture types
        this.colorPalette = [
            '#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#6366f1',
            '#84cc16', '#a855f7', '#22c55e', '#eab308', '#0ea5e9',
            '#d946ef', '#65a30d', '#f43f5e', '#facc15', '#0891b2'
        ];
        this.fixtureColors = new Map();
        this.fixtureTypes = new Set();
        
        // Setup
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Mouse events for dragging and selection
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.onMouseUp.bind(this));
        
        // Click event for fixture selection (with Ctrl key for multi-select)
        this.canvas.addEventListener('click', this.onCanvasClick.bind(this));
        
        // Mouse wheel for zooming
        this.canvas.addEventListener('wheel', this.onWheel.bind(this));
        
        // Prevent context menu
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    loadCanvasData(data) {
        console.log('📊 Loading canvas data:', data);
        
        this.fixtures = data.fixtures;
        this.blueprint = data.blueprint;
        this.bounds = data.bounds;
        
        // Extract unique fixture types and assign colors
        this.assignFixtureColors();
        
        // Debug: Show fixture sizes
        console.log('📐 Fixture sizes received:');
        this.fixtures.slice(0, 5).forEach(f => {
            console.log(`  • ${f.name}: width=${f.width || 'MISSING'}, height=${f.height || 'MISSING'}`);
        });
        
        // Auto-fit to canvas
        this.fitToCanvas();
        
        // Render immediately (removed animation effect)
        this.render();
        
        console.log(`✅ Loaded ${this.fixtures.length} fixtures with ${this.fixtureTypes.size} types`);
    }
    
    assignFixtureColors() {
        // Extract fixture type from name (e.g., "VC_FIXTURE_LARGE_1" -> "VC_FIXTURE_LARGE")
        this.fixtures.forEach(fixture => {
            const fixtureType = this.getFixtureType(fixture.name);
            this.fixtureTypes.add(fixtureType);
        });
        
        // Assign colors to each fixture type
        const types = Array.from(this.fixtureTypes).sort();
        types.forEach((type, index) => {
            const colorIndex = index % this.colorPalette.length;
            this.fixtureColors.set(type, this.colorPalette[colorIndex]);
        });
    }
    
    getFixtureType(fixtureName) {
        // Remove trailing numbers and underscores to get the base type
        // e.g., "VC_FIXTURE_LARGE_1" -> "VC_FIXTURE_LARGE"
        return fixtureName.replace(/_\d+$/, '');
    }
    
    getFixtureColor(fixtureName) {
        const type = this.getFixtureType(fixtureName);
        return this.fixtureColors.get(type) || '#60a5fa';
    }
    
    fitToCanvas() {
        if (!this.bounds) return;
        
        const padding = 50;
        const canvasWidth = this.canvas.width - 2 * padding;
        const canvasHeight = this.canvas.height - 2 * padding;
        
        const scaleX = canvasWidth / this.bounds.width;
        const scaleY = canvasHeight / this.bounds.height;
        
        this.scale = Math.min(scaleX, scaleY) * 0.8;
        
        // Center the view
        // Note: Y-axis is flipped (negated scale), so we need to negate the Y offset
        this.offsetX = this.canvas.width / 2 - (this.bounds.min_x + this.bounds.width / 2) * this.scale;
        this.offsetY = this.canvas.height / 2 + (this.bounds.min_y + this.bounds.height / 2) * this.scale;
    }
    
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Save context
        this.ctx.save();
        
        // Apply transform
        this.ctx.translate(this.offsetX, this.offsetY);
        // Flip Y-axis: DXF has Y+ going UP, Canvas has Y+ going DOWN
        this.ctx.scale(this.scale, -this.scale);
        
        // Draw blueprint (walls, lines, etc.)
        this.drawBlueprint();
        
        // Draw fixtures
        this.fixtures.forEach(fixture => {
            this.drawFixture(fixture);
        });
        
        // Restore context
        this.ctx.restore();
        
        // Draw UI overlay
        this.drawOverlay();
    }
    
    drawBlueprint() {
        this.ctx.strokeStyle = '#e5e7eb';
        this.ctx.lineWidth = 1 / this.scale;
        
        this.blueprint.forEach(entity => {
            const type = entity.type;
            const data = entity.data;
            
            if (type === 'LINE') {
                this.ctx.beginPath();
                this.ctx.moveTo(data.start[0], data.start[1]);
                this.ctx.lineTo(data.end[0], data.end[1]);
                this.ctx.stroke();
            }
            else if (type === 'LWPOLYLINE' || type === 'POLYLINE') {
                if (data.points && data.points.length > 0) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(data.points[0][0], data.points[0][1]);
                    for (let i = 1; i < data.points.length; i++) {
                        this.ctx.lineTo(data.points[i][0], data.points[i][1]);
                    }
                    if (data.closed) {
                        this.ctx.closePath();
                    }
                    this.ctx.stroke();
                }
            }
            else if (type === 'CIRCLE') {
                this.ctx.beginPath();
                this.ctx.arc(data.center[0], data.center[1], data.radius, 0, Math.PI * 2);
                this.ctx.stroke();
            }
            else if (type === 'ARC') {
                this.ctx.beginPath();
                const startAngle = data.start_angle * Math.PI / 180;
                const endAngle = data.end_angle * Math.PI / 180;
                this.ctx.arc(data.center[0], data.center[1], data.radius, startAngle, endAngle);
                this.ctx.stroke();
            }
        });
    }
    
    drawFixture(fixture) {
        const [x, y] = fixture.position;
        const isSelected = this.selectedFixture === fixture;
        const isMultiSelected = this.selectedFixtures.some(f => f.name === fixture.name);
        // Removed AI visual effects - no longer showing green pulse or badges
        
        // Use actual fixture size (or default if not available)
        const width = fixture.width || 300;
        const height = fixture.height || 300;
        const rotation = fixture.rotation || 0;
        const scaleX = fixture.scale_x || 1;
        const scaleY = fixture.scale_y || 1;
        
        // Get block bounding box offset from origin
        // In DXF, blocks can have content that doesn't start at (0,0)
        // We need to draw the block at its min position, not centered
        const blockMinX = fixture.block_min_x !== undefined ? fixture.block_min_x : 0;
        const blockMinY = fixture.block_min_y !== undefined ? fixture.block_min_y : 0;
        
        // Debug first few fixtures
        if (!this._debuggedFixtures) this._debuggedFixtures = 0;
        if (this._debuggedFixtures < 3) {
            console.log(`🎨 Drawing fixture #${this._debuggedFixtures + 1}: ${fixture.name}`);
            console.log(`   Position: [${x}, ${y}], Scale: ${this.scale}`);
            console.log(`   Drawing rect: width=${width}mm, height=${height}mm`);
            console.log(`   Fixture scale: (${scaleX}, ${scaleY})`);
            console.log(`   On canvas: ${width * this.scale}px × ${height * this.scale}px`);
            this._debuggedFixtures++;
        }
        
        // Save context for transformation
        this.ctx.save();

        // Compute insertion (translation) point. Keep existing clinic adjustment as a fallback
        // but prefer using a consistent combined transform matrix below.
        let translateX = x;
        let translateY = y;
        const isClinic = fixture.name.toUpperCase().includes('CLINIC');
        if (isClinic && scaleX < 0) {
            if (rotation === 0) {
                translateX = x ;
            } else if (rotation === 0) {
                translateX = x - width;
            }
        }

        // Build a single local transform matrix (maps block-local coords -> world coords):
        // [ a c e ]   [ scaleX * cos  -scaleY * sin  translateX ]
        // [ b d f ] = [ scaleX * sin   scaleY * cos   translateY ]
        // This handles mirroring (negative scaleX/scaleY) naturally.
        const rad = rotation * Math.PI / 180;
        const cos = Math.cos(rad);
        const sin = Math.sin(rad);
        const a = scaleX * cos;
        const b = scaleX * sin;
        const c = -scaleY * sin;
        const d = scaleY * cos;
        const e = translateX;
        const f = translateY;

        // Multiply the current (world) transform by the local matrix so subsequent draws
        // are placed correctly. We use transform(a,b,c,d,e,f) which multiplies CTM by M.
        this.ctx.transform(a, b, c, d, e, f);
        
        // Draw rectangle at the block's bounding box position
        // The block content starts at (blockMinX, blockMinY) in local coordinates
        // After transformations, this becomes the rectangle origin
        let rectX = blockMinX;
        let rectY = blockMinY;
        const rectWidth = width;
        const rectHeight = height;
        // With the combined matrix above we no longer need manual flipping of rect offsets;
        // negative scales are applied by the matrix and entity coordinates can be drawn
        // directly in block-local coordinates.
        
        // Get color for this fixture type
        const baseColor = this.getFixtureColor(fixture.name);
        let fillColor = baseColor;
        let strokeColor = this.darkenColor(baseColor, 20);
        
        // Highlight for dragging or multi-selection (removed AI update highlighting)
        if (isSelected) {
            fillColor = '#fbbf24';  // Yellow when dragging
            strokeColor = '#d97706';  // Dark yellow
        } else if (isMultiSelected) {
            fillColor = '#60a5fa';  // Blue when selected for AI rearrangement
            strokeColor = '#2563eb';  // Dark blue
        }
        
        // If block entity geometry exists, draw it to reproduce the exact block
        const blockEntities = fixture.block_entities || fixture.blockEntities || fixture.entities;

        // Draw background fill (keeps consistent visual even when block entities are present)
        this.ctx.fillStyle = fillColor;
        this.ctx.fillRect(rectX, rectY, rectWidth, rectHeight);

        if (Array.isArray(blockEntities) && blockEntities.length > 0) {
            // Draw block entities in local block coordinates. We translate to rectX,rectY
            // and draw entity coordinates offset by blockMin to keep alignment.
            this.ctx.save();
            this.ctx.translate(rectX, rectY);

            // Stroke style for block content (contrasts with background)
            const contentStroke = this.darkenColor(baseColor, 40);
            this.ctx.lineWidth = Math.max(1, (isSelected ? 2 : 1) / this.scale);
            this.ctx.strokeStyle = contentStroke;
            this.ctx.fillStyle = contentStroke;

            blockEntities.forEach(entity => {
                const type = (entity.type || '').toUpperCase();

                if (type === 'LINE') {
                    const s = entity.start || entity.start_point || entity.p1;
                    const e = entity.end || entity.end_point || entity.p2;
                    if (s && e) {
                        this.ctx.beginPath();
                        this.ctx.moveTo(s[0] - blockMinX, s[1] - blockMinY);
                        this.ctx.lineTo(e[0] - blockMinX, e[1] - blockMinY);
                        this.ctx.stroke();
                    }
                }
                else if (type === 'LWPOLYLINE' || type === 'POLYLINE' || type === 'POLYGON') {
                    const pts = entity.points || entity.vertices || entity.coords || [];
                    if (pts && pts.length > 0) {
                        this.ctx.beginPath();
                        this.ctx.moveTo(pts[0][0] - blockMinX, pts[0][1] - blockMinY);
                        for (let i = 1; i < pts.length; i++) {
                            this.ctx.lineTo(pts[i][0] - blockMinX, pts[i][1] - blockMinY);
                        }
                        if (entity.closed || entity.closed === true) {
                            this.ctx.closePath();
                            // Optionally fill closed polylines with slightly darker fill
                            this.ctx.fillStyle = this.darkenColor(baseColor, 30);
                            this.ctx.fill();
                        }
                        this.ctx.stroke();
                    }
                }
                else if (type === 'CIRCLE') {
                    const c = entity.center || entity.c || entity.center_point;
                    const r = entity.radius || entity.r;
                    if (c && typeof r === 'number') {
                        this.ctx.beginPath();
                        this.ctx.arc(c[0] - blockMinX, c[1] - blockMinY, r, 0, Math.PI * 2);
                        this.ctx.stroke();
                    }
                }
                else if (type === 'ARC') {
                    const c = entity.center || entity.c || entity.center_point;
                    const r = entity.radius || entity.r;
                    const startAngle = (entity.start_angle !== undefined ? entity.start_angle : entity.start) * Math.PI / 180;
                    const endAngle = (entity.end_angle !== undefined ? entity.end_angle : entity.end) * Math.PI / 180;
                    if (c && typeof r === 'number') {
                        this.ctx.beginPath();
                        this.ctx.arc(c[0] - blockMinX, c[1] - blockMinY, r, startAngle, endAngle);
                        this.ctx.stroke();
                    }
                }
                // Add other entity types as needed (ELLIPSE, TEXT, INSERT) in future
            });

            this.ctx.restore();
        }

        // Border (always drawn after block content)
        this.ctx.strokeStyle = strokeColor;
        this.ctx.lineWidth = (isSelected ? 4 : 2) / this.scale;
        this.ctx.strokeRect(rectX, rectY, rectWidth, rectHeight);
        
        // Reset rotation for label
        if (rotation !== 0) {
            this.ctx.rotate(-rotation * Math.PI / 180);
        }
        
        // Only show dimensions for selected fixture
        if (isSelected) {
            this.ctx.scale(1/this.scale, 1/this.scale);
            
            this.ctx.fillStyle = '#000';
            this.ctx.font = 'bold 12px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            
            // Fixture name
            const name = fixture.name.substring(0, 20);
            this.ctx.fillText(name, 0, 0);
            
            // Show dimensions
            this.ctx.font = '10px Arial';
            this.ctx.fillStyle = '#666';
            this.ctx.fillText(`${Math.round(width)} × ${Math.round(height)} mm`, 0, 15);
        }
        
        this.ctx.restore();
    }
    
    drawOverlay() {
        // Draw scale indicator
        this.ctx.fillStyle = '#666';
        this.ctx.font = '12px monospace';
        this.ctx.fillText(`Scale: ${(this.scale * 100).toFixed(0)}%`, 10, 20);
        
        // Draw fixture legend
        this.drawFixtureLegend();
    }
    
    drawFixtureLegend() {
        const legendX = this.canvas.width - 250;
        const legendY = 10;
        const legendWidth = 240;
        const itemHeight = 25;
        const dotSize = 12;
        
        const types = Array.from(this.fixtureTypes).sort();
        const legendHeight = types.length * itemHeight + 30;
        
        // Draw legend background
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        this.ctx.strokeStyle = '#d1d5db';
        this.ctx.lineWidth = 1;
        this.ctx.fillRect(legendX, legendY, legendWidth, legendHeight);
        this.ctx.strokeRect(legendX, legendY, legendWidth, legendHeight);
        
        // Draw legend title
        this.ctx.fillStyle = '#374151';
        this.ctx.font = 'bold 14px Arial';
        this.ctx.fillText('Fixture Types', legendX + 10, legendY + 20);
        
        // Draw each fixture type with color dot
        this.ctx.font = '12px Arial';
        types.forEach((type, index) => {
            const y = legendY + 40 + index * itemHeight;
            const color = this.fixtureColors.get(type);
            
            // Draw color dot
            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.arc(legendX + 15, y, dotSize / 2, 0, 2 * Math.PI);
            this.ctx.fill();
            
            // Draw border around dot
            this.ctx.strokeStyle = this.darkenColor(color, 20);
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
            
            // Draw fixture type name
            this.ctx.fillStyle = '#374151';
            const displayName = type.replace(/_/g, ' ');
            this.ctx.fillText(displayName, legendX + 30, y + 4);
        });
    }
    
    darkenColor(hexColor, percent) {
        // Convert hex to RGB
        const num = parseInt(hexColor.slice(1), 16);
        const r = (num >> 16) - Math.round((num >> 16) * percent / 100);
        const g = ((num >> 8) & 0x00FF) - Math.round(((num >> 8) & 0x00FF) * percent / 100);
        const b = (num & 0x0000FF) - Math.round((num & 0x0000FF) * percent / 100);
        
        const newR = Math.max(0, r);
        const newG = Math.max(0, g);
        const newB = Math.max(0, b);
        
        return `#${(newR << 16 | newG << 8 | newB).toString(16).padStart(6, '0')}`;
    }
    
    blendColors(color1, color2, ratio) {
        // Blend two hex colors with given ratio (0 = color1, 1 = color2)
        const num1 = parseInt(color1.slice(1), 16);
        const num2 = parseInt(color2.slice(1), 16);
        
        const r1 = num1 >> 16;
        const g1 = (num1 >> 8) & 0x00FF;
        const b1 = num1 & 0x0000FF;
        
        const r2 = num2 >> 16;
        const g2 = (num2 >> 8) & 0x00FF;
        const b2 = num2 & 0x0000FF;
        
        const r = Math.round(r1 * (1 - ratio) + r2 * ratio);
        const g = Math.round(g1 * (1 - ratio) + g2 * ratio);
        const b = Math.round(b1 * (1 - ratio) + b2 * ratio);
        
        return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
    }
    
    // Mouse Events
    
    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;
        
        // Track mouse down time to detect clicks vs drags
        this.mouseDownTime = Date.now();
        this.mouseDownPos = [canvasX, canvasY];
        
        // Transform to world coordinates (Y-axis is flipped with negative scale)
        const worldX = (canvasX - this.offsetX) / this.scale;
        const worldY = -(canvasY - this.offsetY) / this.scale;
        
        // Check if clicked on a fixture
        const fixture = this.getFixtureAt(worldX, worldY);
        
        if (fixture) {
            this.selectedFixture = fixture;
            this.isDragging = true;
            this.dragStartPos = [...fixture.position];
            this.dragStartCanvasPos = [canvasX, canvasY];
            
            // Update UI
            document.getElementById('selected-fixture').textContent = fixture.name;
            document.getElementById('start-coords').textContent = 
                `(${fixture.position[0].toFixed(2)}, ${fixture.position[1].toFixed(2)})`;
            
            this.render();
        }
    }
    
    onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;
        
        if (this.isDragging && this.selectedFixture) {
            // Calculate delta in canvas space
            const deltaCanvasX = canvasX - this.dragStartCanvasPos[0];
            const deltaCanvasY = canvasY - this.dragStartCanvasPos[1];
            
            // Convert to world space (Y-axis is flipped)
            const deltaWorldX = deltaCanvasX / this.scale;
            const deltaWorldY = -deltaCanvasY / this.scale;
            
            // Update fixture position
            this.selectedFixture.position = [
                this.dragStartPos[0] + deltaWorldX,
                this.dragStartPos[1] + deltaWorldY
            ];
            
            // Update UI
            const [newX, newY] = this.selectedFixture.position;
            document.getElementById('current-coords').textContent = 
                `(${newX.toFixed(2)}, ${newY.toFixed(2)})`;
            
            const dx = newX - this.dragStartPos[0];
            const dy = newY - this.dragStartPos[1];
            document.getElementById('delta-coords').textContent = 
                `(${dx.toFixed(2)}, ${dy.toFixed(2)})`;
            
            const distance = Math.sqrt(dx*dx + dy*dy);
            document.getElementById('distance-moved').textContent = 
                `${distance.toFixed(2)} mm`;
            
            // Re-render
            this.render();
        }
    }
    
    async onMouseUp(e) {
        if (!this.isDragging || !this.selectedFixture) {
            this.isDragging = false;
            return;
        }
        
        this.isDragging = false;
        
        const endPos = [...this.selectedFixture.position];
        
        // Check if actually moved
        const dx = endPos[0] - this.dragStartPos[0];
        const dy = endPos[1] - this.dragStartPos[1];
        const distance = Math.sqrt(dx*dx + dy*dy);
        
        if (distance < 1) {
            // Not moved significantly, ignore
            return;
        }
        
        console.log(`📍 Fixture moved: ${this.selectedFixture.name}`);
        console.log(`   From: (${this.dragStartPos[0].toFixed(2)}, ${this.dragStartPos[1].toFixed(2)})`);
        console.log(`   To:   (${endPos[0].toFixed(2)}, ${endPos[1].toFixed(2)})`);
        console.log(`   Delta: (${dx.toFixed(2)}, ${dy.toFixed(2)})`);
        
        // Add to prompt list (if function is available from HTML)
        if (typeof window.addMovementPrompt === 'function') {
            window.addMovementPrompt(
                this.selectedFixture.name,
                this.dragStartPos,
                endPos,
                [dx, dy]
            );
        }
        
        // Also send to backend for real-time updates (optional - can be disabled)
        // await this.updateFixturePosition(
        //     this.selectedFixture.name,
        //     this.dragStartPos,
        //     endPos,
        //     [dx, dy]
        // );
    }
    
    onCanvasClick(e) {
        // Only process as click if mouse hasn't moved much and was quick
        const timeSinceDown = Date.now() - this.mouseDownTime;
        if (timeSinceDown > 300) return; // Was a drag, not a click
        
        const rect = this.canvas.getBoundingClientRect();
        const canvasX = e.clientX - rect.left;
        const canvasY = e.clientY - rect.top;
        
        // Check if mouse moved significantly (more than 5px = drag)
        if (this.mouseDownPos) {
            const dx = canvasX - this.mouseDownPos[0];
            const dy = canvasY - this.mouseDownPos[1];
            const distance = Math.sqrt(dx*dx + dy*dy);
            if (distance > 5) return; // Was a drag
        }
        
        // Transform to world coordinates
        const worldX = (canvasX - this.offsetX) / this.scale;
        const worldY = -(canvasY - this.offsetY) / this.scale;
        
        // Check if clicked on a fixture
        const fixture = this.getFixtureAt(worldX, worldY);
        
        if (!fixture) {
            // Clicked empty space - clear selection if not using Ctrl
            if (!e.ctrlKey && !e.metaKey) {
                this.selectedFixtures = [];
                this.render();
                if (typeof window.onFixtureClicked === 'function') {
                    // Update prompt to show no selection
                    window.onFixtureClicked(null, null);
                }
            }
            return;
        }
        
        // Ctrl/Cmd key for multi-select
        if (e.ctrlKey || e.metaKey) {
            // Toggle selection
            const index = this.selectedFixtures.findIndex(f => f.name === fixture.name);
            if (index >= 0) {
                // Deselect
                this.selectedFixtures.splice(index, 1);
            } else {
                // Add to selection
                this.selectedFixtures.push(fixture);
            }
        } else {
            // Single select (replace selection)
            this.selectedFixtures = [fixture];
        }
        
        // Notify parent page
        if (typeof window.onFixtureClicked === 'function') {
            window.onFixtureClicked(fixture.name, fixture.position);
        }
        
        // Redraw to show selection highlights
        this.render();
    }
    
    onWheel(e) {
        e.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Zoom factor
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        const newScale = this.scale * zoomFactor;
        
        // Limit scale
        if (newScale < this.minScale || newScale > this.maxScale) {
            return;
        }
        
        // Zoom towards mouse position (Y-axis is flipped)
        const worldX = (mouseX - this.offsetX) / this.scale;
        const worldY = -(mouseY - this.offsetY) / this.scale;
        
        this.scale = newScale;
        
        this.offsetX = mouseX - worldX * this.scale;
        this.offsetY = mouseY + worldY * this.scale;
        
        this.render();
    }
    
    // Helper Methods
    
    getFixtureAt(worldX, worldY) {
        // Check from top to bottom (reverse order for proper z-index)
        for (let i = this.fixtures.length - 1; i >= 0; i--) {
            const fixture = this.fixtures[i];
            const [fx, fy] = fixture.position;
            const width = fixture.width || 300;
            const height = fixture.height || 300;
            const rotation = fixture.rotation || 0;
            const scaleX = fixture.scale_x || 1;
            const scaleY = fixture.scale_y || 1;
            
            // Get block bounding box offset (same as in drawFixture)
            const blockMinX = fixture.block_min_x !== undefined ? fixture.block_min_x : 0;
            const blockMinY = fixture.block_min_y !== undefined ? fixture.block_min_y : 0;
            
            // Calculate the actual bounding box in world coordinates
            // We need to apply the same transformation matrix as drawFixture
            
            // Handle clinic special case
            let translateX = fx;
            let translateY = fy;
            const isClinic = fixture.name.toUpperCase().includes('CLINIC');
            if (isClinic && scaleX < 0) {
                if (rotation === 0) {
                    translateX = fx;
                } else if (rotation === 90) {
                    translateX = fx - height;
                }
            }
            
            // Build transformation matrix
            const rad = rotation * Math.PI / 180;
            const cos = Math.cos(rad);
            const sin = Math.sin(rad);
            const a = scaleX * cos;
            const b = scaleX * sin;
            const c = -scaleY * sin;
            const d = scaleY * cos;
            const e = translateX;
            const f = translateY;
            
            // Transform click point from world to local coordinates
            // Inverse transformation: [x', y'] = M^-1 * [x, y]
            const det = a * d - b * c;
            if (Math.abs(det) < 0.0001) continue; // Skip degenerate transformations
            
            const invA = d / det;
            const invB = -b / det;
            const invC = -c / det;
            const invD = a / det;
            const invE = (c * f - d * e) / det;
            const invF = (b * e - a * f) / det;
            
            const localX = invA * worldX + invC * worldY + invE;
            const localY = invB * worldX + invD * worldY + invF;
            
            // Check if local point is inside the bounding box
            // The box is drawn from (blockMinX, blockMinY) with size (width, height)
            if (localX >= blockMinX && localX <= blockMinX + width &&
                localY >= blockMinY && localY <= blockMinY + height) {
                return fixture;
            }
        }
        
        return null;
    }
    
    async updateFixturePosition(name, startPos, endPos, delta) {
        try {
            const response = await fetch('/move_fixture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    fixture_name: name,
                    start_position: startPos,
                    end_position: endPos,
                    delta: delta
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Backend updated successfully');
                
                // Show success message
                if (typeof showStatus === 'function') {
                    showStatus(`✅ Moved ${name}`, 'success');
                }
            } else {
                console.error('❌ Backend update failed:', result.error);
            }
            
        } catch (error) {
            console.error('❌ Error updating fixture:', error);
        }
    }
    
    // View Controls
    
    clearSelections() {
        this.selectedFixtures = [];
        this.render();
    }
    
    zoomIn() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        const worldX = (centerX - this.offsetX) / this.scale;
        const worldY = (centerY - this.offsetY) / this.scale;
        
        this.scale = Math.min(this.scale * 1.2, this.maxScale);
        
        this.offsetX = centerX - worldX * this.scale;
        this.offsetY = centerY - worldY * this.scale;
        
        this.render();
    }
    
    zoomOut() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        const worldX = (centerX - this.offsetX) / this.scale;
        const worldY = (centerY - this.offsetY) / this.scale;
        
        this.scale = Math.max(this.scale / 1.2, this.minScale);
        
        this.offsetX = centerX - worldX * this.scale;
        this.offsetY = centerY - worldY * this.scale;
        
        this.render();
    }
    
    resetView() {
        this.fitToCanvas();
        this.render();
    }
}
