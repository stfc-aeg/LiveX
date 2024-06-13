import { useState, useEffect, useCallback } from 'react';

function ClickableImage(props){
    // Endpoint is used to send selected coordinates, index refers to image path of multiple cameras
    // 'imgSrc' is the image data. this could be from an endpoint e.g.: liveDataEndpoint?.image.data
    // fullpath is the path the coordinates should be written to, no trailing or leading slashes
    // paramToUpdate is the parameter you are updating. The 'final' part of the address
    // maximiseAxis is 'x' or 'y' and overrides user selection to the bounds of that axis
    // rectOutlineColour is a string representing the desired colour of the selection border
    // rectRgbaProperties is the fill style for the polygon. format: 'rgba(R,G,B,A)'.
    // rgba properties are 0->255 or 0->1 for alpha (transparency)
    const {endpoint, imgSrc, fullpath, paramToUpdate, maximiseAxis=null, rectOutlineColour='white', rectRgbaProperties='rgba(255,255,255,0.33)' } = props;

    const maxAxis = maximiseAxis ? maximiseAxis.toLowerCase() : null;

    const [imgData, changeImgData] = useState([{}]);
    useEffect(() => {
        changeImgData(`data:image/jpg;base64,${imgSrc}`);
      }, [imgSrc]);

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
        const canvas = document.getElementById('canvas');
        if (maxAxis === "x") {
          minX = 0;
          maxX = canvas.clientWidth;
        } else if (maxAxis === "y") {
          minY = 0;
          maxY = canvas.clientHeight;
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
    }, [startPoint, endPoint]);

    const handleMouseDown = useCallback(e => {
      // First click does nothing by itself
      const point = getPoint(e);
      setStartPoint(point);
      setEndPoint(point);
    }, [getPoint]);

    const handleMouseMove = useCallback(e => {
        if (startPoint) {
            let point = getPoint(e);
            setEndPoint(point);
            calculateRectangle();
        }
    }, [startPoint, getPoint, calculateRectangle]);

    const handleMouseUp = useCallback(e => {
      if (startPoint) {
        calculateRectangle();

        setStartPoint(null); // Reset start point after creating rectangle
        setEndPoint(null); // Resetting end point prevents handleMouseMove drawing more rectangles

        // Send the coordinate data
        const sendVal = {[paramToUpdate]: coords};
        endpoint.put(sendVal, fullpath);
        setPoints([]);
      }
    }, [startPoint, getPoint, calculateRectangle]);
    
    // Only insert polygon tags if there's enough entries in the array
    return (
      <div style={{position:'relative', display:'inline-block',
      maxWidth:'100%', maxHeight:'100%'}}>
        <svg
            id="canvas" 
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
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
            : null}
        </svg>
        <img src={imgData} style={{
          display:'block',
          maxWidth:'100%',
          maxHeight:'100%'
          }}></img>
      </div>
    );
  };
  
export default ClickableImage;