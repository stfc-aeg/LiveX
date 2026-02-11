import { useState, useEffect, useRef, useCallback } from 'react';

function ClickableImage(props){
    /*
    - id is a string for the purpose of the image. This is used for the canvas - if you have more
      than one ClickableImage on a single page, you will need a unique id for its canvas.
    - endpoint is used to send selected coordinates, index refers to image path of multiple cameras
    - coordsPath is the path the coordinates should be written to, no trailing or leading slashes
    - coordsParam is the parameter you are updating. The 'final' part of the address
    - maximiseAxis is 'x' or 'y' and overrides user selection to the bounds of that axis
    - valuesAsPercentages changes output from pixel values to relative percentage selected.
      For example, x values  100-120 on a 300px-wide image. This returns [33.33,40], not [100,120].
    - rectOutlineColour is a string representing the desired colour of the selection border
    - rectRgbaProperties is the fill style for the polygon. format: 'rgba(R,G,B,A)'.
      rgba properties are 0->255 or 0->1 for alpha (transparency)
    */
    const {id, endpoint, imgPath, coordsPath, coordsParam,
      maximiseAxis=null, valuesAsPercentages=false, rectOutlineColour='white', rectRgbaProperties='rgba(255,255,255,0.33)'
    } = props;

    const svgId = `canvas-${id}`;  // canvas id
    const maxAxis = maximiseAxis ? maximiseAxis.toLowerCase() : null;

    const buttons = {
      left: 0,
      middle: 1,
      right: 2
    }

    const [imgData, changeImgData] = useState(null);

    const refreshImage = useCallback(() => {
        endpoint.get(imgPath, {responseType: "blob"})
        .then(result => {
            URL.revokeObjectURL(imgData);  // memory management
            const img_url = URL.createObjectURL(result);
            changeImgData(img_url);
            // endpoint.refreshData();
        }).catch((error) => {
            console.error("IMAGE GET FAILED: ", error);
            changeImgData(null);
        })
    }, [endpoint.updateFlag]);

    useEffect(() => {
        let timer_id;
        timer_id = setInterval(refreshImage, 950);
        return () => clearInterval(timer_id);
    }, [refreshImage]);

    // Initialize some states to keep track of points clicked
    const [startPoint, setStartPoint] = useState([]);
    const [endPoint, setEndPoint] = useState([]);
    const [points, setPoints] = useState([]);
    const [coords, setCoords] = useState([]);

    // Both mouseDown and mouseUp need this
    const getPoint = useCallback(e => {
      // Event handling, get bounds of what the user clicked on and calculate from top-left
      const bounds = e.target.getBoundingClientRect();
      const x = e.clientX - bounds.left;
      const y = e.clientY - bounds.top;

      return [x, y];
    }, []);

    const calculateRectangle = useCallback(() => {
      // Lists of x and y coordinates
      const xCoords = [startPoint[0], endPoint[0]];
      const yCoords = [startPoint[1], endPoint[1]];

      // Get minimums and maximums for next step
      let minX = Math.min(...xCoords);
      let maxX = Math.max(...xCoords);
      let minY = Math.min(...yCoords);
      let maxY = Math.max(...yCoords);

      // Handle the 'maxAxis' feature - which ensures that axis is fully selected
      const canvas = document.getElementById(svgId);
      if (canvas)
      {
        if (maxAxis === "x")
        {
          minX = 0;
          maxX = canvas.clientWidth;
        } else if (maxAxis === "y")
        {
          minY = 0;
          maxY = canvas.clientHeight;
        }
      }

      // The polygon draws from the first entry. Top-left is default here, going clockwise
      const rectanglePoints = [
        [minX, minY], // Top left
        [maxX, minY], // Top right
        [maxX, maxY], // Bottom right
        [minX, maxY], // Bottom left
      ];

      setPoints(rectanglePoints);
      // Coordinates are processed in live_data/controller.py as
      // [[x_lower, x_upper], [y_lower, y_upper]]
      setCoords([[minX, maxX], [minY, maxY]]);
    }, [startPoint, endPoint, maxAxis]);

    //  Handle context menu = handle right click
    const handleContextMenu = useCallback(e => {
      const isRectangle = startPoint || endPoint || points.length > 0;

      if (isRectangle)
      {
        // Cancel context if already rectangle
        e.preventDefault();
        // Reset rectangle
        setStartPoint(null);
        setEndPoint(null);
        setPoints([]);
        setCoords([]);
      }
      // Otherwise open context as normal
    })

    const handleMouseDown = useCallback(e => {
      // First press sets start for when mouse moves
      if (e.button===buttons.left)  // Left click only
      {
        const point = getPoint(e);
        setStartPoint(point);
        setEndPoint(point);
      }

    }, [getPoint]);

    const handleMouseMove = useCallback(e => {
      if (startPoint)
      {
        let point = getPoint(e);
        setEndPoint(point);
        calculateRectangle();
      }
    }, [startPoint, getPoint, calculateRectangle]);

    const handleMouseUp = useCallback(e => {
      if (startPoint) 
      {
        calculateRectangle();

        setStartPoint(null); // Reset start point after creating rectangle
        setEndPoint(null); // Resetting end point prevents handleMouseMove drawing more rectangles

        // Get data to send
        var sendData = coords;

        // Adjust to percentages if needed
        if (valuesAsPercentages)
        {
          let canvas = document.getElementById(svgId);
          let width = canvas.clientWidth;
          let height = canvas.clientHeight;

          // Calculate new percentage coordinates to 2 d.p.
          let xMin = parseFloat(((coords[0][0] / width) * 100).toFixed(2));
          let xMax = parseFloat(((coords[0][1] / width) * 100).toFixed(2));
          let yMin = parseFloat(((coords[1][0] / height) * 100).toFixed(2));
          let yMax = parseFloat(((coords[1][1] / height) * 100).toFixed(2));
          // console.log("coords:", coords);
          sendData = [[xMin, xMax], [yMin, yMax]];
          // setCoords([[xMin, xMax], [yMin, yMax]]);
          // console.log("percentage data:", sendData);
        }

        // Send the coordinate data
        const sendVal = {[coordsParam
        ]: sendData};
        // console.log("sendval:", JSON.stringify(sendVal));
        endpoint.put(sendVal, coordsPath);
        setPoints([]);
      }
    }, [startPoint, getPoint, calculateRectangle]);

    // Only insert polygon tags if there's enough entries in the array
    return (
      <div>
        {imgData ? (
          <div style={{position:'relative', display:'block',
          width:'100%', height:'auto'}}>
            <svg
              id={svgId}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onContextMenu={handleContextMenu}
              style={{position:'absolute',top:0,left:0,width:'100%',height:'100%'}}>
              {points.length === 4 ?
                <polygon
                  points={points.map(point => point.join(",")).join(" ")}
                  style={{
                          pointerEvents:'none', // Unclickable
                          fill: rectRgbaProperties,
                          stroke: rectOutlineColour // border
                        }}
                  />
                : null
              }
            </svg>
            <img
              id='img'
              src={imgData}
              style={{
              display:'block',
              width:'100%',
              height:'auto',
              minHeight:'18px'  // height of 'no image found' icon. prevent 'flickering' when no img
              }}
              alt="Live camera feed"
              />
              </div>
          ) : (
            <div>No Image Available</div>
          )}
      </div>
    );
  };
  
export default ClickableImage;